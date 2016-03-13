# -*- coding: utf-8 -*-
"""
Almost everything in this module is copied from
:mod:`sphinx.ext.workflow_diagram` and only slightly modified.
"""

from inspect import isclass

from docutils.nodes import paragraph
from kotti.workflow import get_workflow
from sphinx.ext.graphviz import graphviz, figure_wrapper

from kotti_sphinx_extensions import KottiAppDirective
from kotti_sphinx_extensions import _resolve_dotted


class WorkflowException(Exception):
    pass


class WorkflowGraph(object):
    """ Given a content object, its class or dotted name, determines the
    workflow in action for the given ``kotti_ini``, and then generates a
    graphviz dot graph for the workflow states and transitions.
    """

    # Default attrs for graphviz
    default_graph_attrs = {
        'rankdir': 'LR',
        'size': '"8.0, 12.0"',
    }
    default_node_attrs = {
        'shape': 'oval',
        # 'style': '"setlinewidth(0.5)"',
    }
    default_edge_attrs = {
        'arrowsize': 0.5,
        # 'style': '"setlinewidth(0.5)"',
    }

    def __init__(self, content):
        """ *content* is either an instance, a class or a dotted name of a class
        assigned to a workflow (or not).  If it's an iterable, only consider the
        first element.
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
        """ States of the associated workflow (if any). """

        wf = self.workflow
        return wf and wf._state_info(self.content) or []

    @property
    def transitions(self):
        """ Transitions of the associated workflow (if any). """

        transitions = []
        for s in self.states:
            transitions.extend(
                self.workflow._get_transitions(self.content,
                                               from_state=s['name']))
        return transitions

    @staticmethod
    def _format_node_attrs(attrs):

        return ','.join(['%s=%s' % x for x in attrs.items()])

    @staticmethod
    def _format_graph_attrs(attrs):

        return ''.join(['%s=%s;\n' % x for x in attrs.items()])

    def generate_dot(self, name, env=None, graph_attrs=None, node_attrs=None,
                     edge_attrs=None):
        """ Generate a graphviz dot graph for the workflow configured for the
        class that was passed in to __init__.

        *name* is the name of the graph.

        *graph_attrs*, *node_attrs*, *edge_attrs* are dictionaries containing
        key/value pairs to pass on as graphviz properties.
        """

        g_attrs = self.default_graph_attrs.copy()
        if graph_attrs is not None:
            g_attrs.update(graph_attrs)

        n_attrs = self.default_node_attrs.copy()
        if node_attrs is not None:
            n_attrs.update(node_attrs)

        e_attrs = self.default_edge_attrs.copy()
        if edge_attrs is not None:
            e_attrs.update(edge_attrs)

        if env:
            g_attrs.update(env.config.workflow_graph_attrs)
            n_attrs.update(env.config.workflow_node_attrs)
            e_attrs.update(env.config.workflow_edge_attrs)

        res = [u'digraph "%s" {' % name, self._format_graph_attrs(g_attrs)]

        for s in self.states:
            this_node_attrs = n_attrs.copy()
            if s['initial']:
                this_node_attrs['peripheries'] = 2
            this_node_attrs['label'] = u'"{} ({})"'.format(
                s['title'],
                s['name'])
            res.append(u'  "{}" [{}];'.format(
                s['name'],
                self._format_node_attrs(this_node_attrs)))

        for t in self.transitions:
            this_edge_attrs = e_attrs.copy()
            this_edge_attrs['label'] = u'"{}"'.format(t.get('title', u''))
            res.append(u'  "{}" -> "{}" [{}];'.format(
                t['from_state'],
                t['to_state'],
                self._format_node_attrs(this_edge_attrs)))

        res.append('}')

        return u'\n'.join(res)


class WorkflowDiagram(KottiAppDirective):
    """ """

    required_arguments = 1
    has_content = False
    directive = 'workflow-diagram'

    def run(self):

        node = graphviz()
        dotted = self.arguments[0].split()[0]

        # Create a graph for ``dotted``.
        try:
            graph = WorkflowGraph(dotted)
        except WorkflowException as err:
            return [node.document.reporter.warning(
                err.args[0], line=self.lineno)]

        node['code'] = graph.generate_dot(self.name)
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

        # schema_data_tableinfo = []
        # for col in TABLE_COLS:
        #     schema_data_tableinfo.append(len(col))
        #
        # schema_data = []
        # schema = _resolve_dotted_name(self.name)
        # for field in schema._fields:
        #     field = schema.get(field)
        #     schema_data.append([
        #         str(field.getName()),
        #         str(field.required),
        #         str(field.searchable),
        #         str(field.type),
        #         str(field.storage.__class__.__name__),
        #         ])
        #
        #     if len(str(field.getName())) > schema_data_tableinfo[0]:
        #         schema_data_tableinfo[0] = len(str(field.getName()))
        #     if len(str(field.required)) > schema_data_tableinfo[1]:
        #         schema_data_tableinfo[1] = len(str(field.required))
        #     if len(str(field.searchable)) > schema_data_tableinfo[2]:
        #         schema_data_tableinfo[2] = len(str(field.searchable))
        #     if len(str(field.type)) > schema_data_tableinfo[3]:
        #         schema_data_tableinfo[3] = len(str(field.type))
        #     if len(str(field.storage.__class__.__name__)) > schema_data_tableinfo[4]:
        #         schema_data_tableinfo[4] = len(str(field.storage.__class__.__name__))
        #
        # result = ViewList()
        # result.append(u'', '<autoatschema>')
        # result.append(u'%s: ``%s``' % (self.name.split('.')[-1], self.name), '<autoatschema>')
        # result.append(u'', '<autoatschema>')
        # for line in self._buildTable('|l|c|c|l|l|', schema_data,
        #                                 schema_data_tableinfo):
        #     result.append(line, '<autoatschema>')
        # result.append(u'', '<autoatschema>')
        node = paragraph()
        # self.state.nested_parse(result, 0, node)
        return node.children

    def _buildTable(self, specs, data, datainfo):
        result = [u'.. tabularcolumns:: '+specs, u'']

        # separator line
        separator_line = ''
        for colnum in datainfo:
            separator_line += '='*colnum
            separator_line += ' '
        separator_line = separator_line[:-1]

        # header
        header = ''
        for pos, col in enumerate(TABLE_COLS):
            header += col+(datainfo[pos]-len(col))*' '
            header += ' '
        header = header[:-1]

        result.append(separator_line)
        result.append(header)
        result.append(separator_line)

        for data_row in data:
            row = ''
            for pos, data_col in enumerate(data_row):
                row += data_col+(datainfo[pos]-len(data_col))*' '
                row += ' '
            result.append(row[:-1])

        result.append(separator_line)
        return result
