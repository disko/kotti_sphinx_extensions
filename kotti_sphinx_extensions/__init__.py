# -*- coding: utf-8 -*-
"""
Almost everything in this module is copied from
:mod:`sphinx.ext.workflow_diagram` and only slightly modified.
"""

from docutils.parsers.rst import Directive
from pyramid.paster import bootstrap
from pyramid.util import DottedNameResolver


kotti_app = None


def _resolve_dotted(maybe_dotted):
    """ Resolve ``maybe_dotted`` to the corresponding class. """

    if not isinstance(maybe_dotted, basestring):
        return maybe_dotted

    return DottedNameResolver().resolve(maybe_dotted)


# noinspection PyAbstractClass
class KottiAppDirective(Directive):
    """ Base class for directives that need a fully setup Kotti application """

    def __init__(self, directive, arguments, options, content, lineno,
                 content_offset, block_text, state, state_machine):

        assert directive == self.directive
        super(KottiAppDirective, self).__init__(
            directive, arguments, options, content, lineno, content_offset,
            block_text, state, state_machine)

        global kotti_app
        if kotti_app is None:
            env = self.state.document.settings.env
            ini = env.config.kotti_ini
            env.app.info('loading Kotti application from %s...' % ini)
            kotti_app = bootstrap(ini)


class GraphvizMixin(object):

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

    @staticmethod
    def _format_node_attrs(attrs):
        return ','.join(['%s=%s' % x for x in attrs.items()])

    @staticmethod
    def _format_graph_attrs(attrs):
        return ''.join(['%s=%s;\n' % x for x in attrs.items()])

    def generate_dot(self, name, env=None,
                     graph_attrs=None, node_attrs=None, edge_attrs=None):
        """ Generate a graphviz dot graph for the workflow configured for the
        class that was passed in to __init__.

        *name* is the name of the graph.

        *graph_attrs*, *node_attrs*, *edge_attrs* are dictionaries containing
        key/value pairs to pass on as graphviz properties.
        """

        graph_attrs = self.default_graph_attrs.copy()
        if graph_attrs is not None:
            graph_attrs.update(graph_attrs)

        node_attrs = self.default_node_attrs.copy()
        if node_attrs is not None:
            node_attrs.update(node_attrs)

        edge_attrs = self.default_edge_attrs.copy()
        if edge_attrs is not None:
            edge_attrs.update(edge_attrs)

        if env:
            graph_attrs.update(env.config.workflow_graph_attrs)
            node_attrs.update(env.config.workflow_node_attrs)
            edge_attrs.update(env.config.workflow_edge_attrs)

        res = [u'digraph "%s" {' % name, self._format_graph_attrs(graph_attrs)]
        res.extend(self.generate_dot_nodes(node_attrs))
        res.extend(self.generate_dot_edges(edge_attrs))
        res.append('}')

        return u'\n'.join(res)

    def generate_dot_nodes(self, node_attrs):
        raise NotImplementedError('Subclasses must implement this method')


def setup(app):
    # setup dependency extionsions
    app.setup_extension('sphinx.ext.graphviz')

    from kotti_sphinx_extensions.workflow import WorkflowDiagram
    app.add_directive('workflow-diagram', WorkflowDiagram)

    from kotti_sphinx_extensions.workflow import WorkflowPermissionMapping
    app.add_directive('workflow-permissionmapping', WorkflowPermissionMapping)

    app.add_config_value('kotti_ini', {}, False),

    app.add_config_value('workflow_graph_attrs', {}, False),
    app.add_config_value('workflow_node_attrs', {}, False),
    app.add_config_value('workflow_edge_attrs', {}, False),
