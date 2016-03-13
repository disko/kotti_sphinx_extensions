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

    return DottedNameResolver(None).resolve(maybe_dotted)


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
            kotti_app = bootstrap(env.config.kotti_ini)


def setup(app):

    from kotti_sphinx_extensions.workflow import WorkflowDiagram
    app.add_directive('workflow-diagram', WorkflowDiagram)

    from kotti_sphinx_extensions.workflow import WorkflowPermissionMapping
    app.add_directive('workflow-permissionmapping', WorkflowPermissionMapping)

    app.add_config_value('kotti_ini', {}, False),

    app.add_config_value('workflow_graph_attrs', {}, False),
    app.add_config_value('workflow_node_attrs', {}, False),
    app.add_config_value('workflow_edge_attrs', {}, False),
