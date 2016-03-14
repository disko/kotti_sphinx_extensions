# -*- coding: utf-8 -*-
"""
Almost everything in this module is copied from
:mod:`sphinx.ext.workflow_diagram` and only slightly modified.
"""

from inspect import isclass

from docutils.nodes import compound
from docutils.statemachine import ViewList
from kotti.workflow import get_workflow
from sphinx.ext.graphviz import figure_wrapper
from sphinx.ext.graphviz import graphviz

from kotti_sphinx_extensions import GraphvizMixin
from kotti_sphinx_extensions import KottiAppDirective
from kotti_sphinx_extensions import _resolve_dotted


class WorkflowException(Exception):
    pass


class Workflow(GraphvizMixin):
    """ Given a content object, its class or dotted name, determines the
    workflow in action for the given ``kotti_ini``.  Provides all data needed
    by directives, e.g. a graphviz dot graph for the workflow states and
    transitions.
    """

    def __init__(self, content):
        """ *content* is either an instance, a class or a dotted name of a class
        assigned to a workflow (or not).  If it's an iterable, only consider the
        fiself.rst element.
        """

        if isinstance(content, (list, tuple, )):
            content = content[0]

        if isinstance(content, basestring):
            self.content = _resolve_dotted(content)()
        elif isclass(content):
            self.content = content()
        else:
            self.content = content

    @property
    def workflow(self):
        """ The associated workflow object. """

        return get_workflow(self.content)

    @property
    def states(self):
        """ States of :meth:`workflow` (if any). """

        wf = self.workflow
        return wf and wf._state_info(self.content) or []

    @property
    def transitions(self):
        """ Transitions of :meth:`workflow` (if any). """

        transitions = []
        for s in self.states:
            transitions.extend(
                self.workflow._get_transitions(self.content,
                                               from_state=s['name']))
        return transitions

    @property
    def permissions(self):
        """ Permissions managed by :meth:`workflow`"""
        perms = []
        for s in self.states:
            for k, v in s['data'].items():
                if k.startswith('role:'):
                    perms.extend(v.split(' '))
        return sorted(list(set(perms)))

    @property
    def roles(self):
        """ Roles managed by :meth:`workflow`"""
        roles = []
        for s in self.states:
            roles.extend([k.split(':')[1] for k in s['data'].keys() if
                          k.startswith('role:')])
        return sorted(list(set(roles)))

    def generate_dot_nodes(self, node_attrs):
        nodes = []
        for s in self.states:
            this_node_attrs = node_attrs.copy()
            if s['initial']:
                this_node_attrs['peripheries'] = 2
            this_node_attrs['label'] = u'"{} ({})"'.format(
                s['title'],
                s['name'])
            nodes.append(u'  "{}" [{}];'.format(
                s['name'],
                self._format_node_attrs(this_node_attrs)))
        return nodes

    def generate_dot_edges(self, edge_attrs):
        edges = []
        for t in self.transitions:
            this_edge_attrs = edge_attrs.copy()
            this_edge_attrs['label'] = u'"{}"'.format(t.get('title', u''))
            edges.append(u'  "{}" -> "{}" [{}];'.format(
                t['from_state'],
                t['to_state'],
                self._format_node_attrs(this_edge_attrs)))
        return edges


class WorkflowDiagram(KottiAppDirective):
    """ """

    required_arguments = 1
    has_content = False
    directive = 'workflow-diagram'

    def run(self):

        node = graphviz()
        dotted = self.arguments[0].split()[0]

        # Get the workflow for ``dotted``.
        try:
            workflow = Workflow(dotted)
        except WorkflowException as err:
            return [node.document.reporter.warning(
                err.args[0], line=self.lineno)]

        node['code'] = workflow.generate_dot(self.name)
        node['options'] = {}
        if 'graphviz_dot' in self.options:
            node['options']['graphviz_dot'] = self.options['graphviz_dot']
        if 'alt' in self.options:
            node['alt'] = self.options['alt']
        if 'inline' in self.options:
            node['inline'] = True

        caption = self.options.get('caption')
        if caption:
            node = figure_wrapper(self, node, caption)

        return [node]


class WorkflowPermissionMapping(KottiAppDirective):
    """ """

    required_arguments = 1
    has_content = False
    directive = 'workflow-permissionmapping'

    def run(self):

        node = compound()
        dotted = self.arguments[0].split()[0]

        # Get the workflow for ``dotted``.
        try:
            workflow = Workflow(dotted)
        except WorkflowException as err:
            return [node.document.reporter.warning(
                err.args[0], line=self.lineno)]

        self.rst = []

        for state in workflow.states:
            # section title
            title = u'Role to Permissions mapping for state {} ({})'.format(
                state['title'], state['name'])
            # self.rst.append(t)
            # self.rst.append(len(t) * '_')
            # self.rst.append('')

            # table
            # table format
            self.rst.append(u'.. tabularcolumns:: |R|{}|'.format(
                u'|'.join(['C'] * len(workflow.permissions)))
            )
            self.rst.append(u'.. csv-table:: {}'.format(title))
            # table header
            thead = ['Roles / Permissions', ]
            thead.extend([c for c in workflow.permissions])
            self.rst.append(u'   :header: {}'.format(
                u','.join(u'"{}"'.format(c) for c in thead)
            ))
            self.rst.append('')
            # table body
            for role in workflow.roles:
                trow = [role, ]
                perms = state['data'].get(u'role:{}'.format(role), u'')
                for p in workflow.permissions:
                    if p in perms:
                        trow.append('Y')
                    else:
                        trow.append('N')
                self.rst.append(u'   {}'.format(
                    u','.join(u'"{}"'.format(c) for c in trow)
                ))

        result = ViewList()
        result.append(u'', self.directive)
        for r in self.rst:
            result.append(r, self.directive)
        result.append(u'', self.directive)

        self.state.nested_parse(result, 0, node)
        return node.children
