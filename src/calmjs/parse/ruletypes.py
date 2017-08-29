# -*- coding: utf-8 -*-
"""
Rule types are used for building descriptions for processing and
regenerating for a given type of AST back into a string.
"""

from collections import namedtuple
from functools import partial

from calmjs.parse.asttypes import Node
from calmjs.parse.asttypes import Elision
from calmjs.parse.asttypes import Identifier

LayoutRuleChunk = namedtuple('LayoutRuleChunk', [
    'rule', 'handler', 'node'])
SourceChunk = namedtuple('SourceChunk', [
    'text', 'lineno', 'colno', 'original'])


def is_empty(value):
    return value in (None, [])


class Rule(object):
    """
    The base type.
    """


class Layout(Rule):
    """
    Layout rules are simply for building markers that either return some
    extraneous fragments or set some flags on the Dispatcher object for
    further usage, so that the pretty printing will look pretty.

    The subclasses will be used as types for the handler lookup (i.e.
    they will serve as keys); for the subclasses to be used as par of
    the definition for the structure of a given asttype, it must be
    instantiated.
    """


class Token(Rule):
    """
    Token rules are callable rules that will directly take part in
    ochestrating the rendering of the given input node, along with the
    walk function and the Dispatcher object that tracks the currently
    executing prettyprint iteration.

    Like the Layout type, Token types must also be instantiated before
    they can be used.
    """

    def __init__(self, attr=None, value=None, pos=0):
        """
        Arguments

        attr
            Should reference some attribute of the referenced Node
        value
            Some value that will be assigned to this token for use in
            the production of chunks
        pos
            The index to be passed to Token.getpos for the correct
            index for the given token map entry.  The text element will
            be used for the lookup first, and typically the correct
            position will be reported on the 0th entry, however for
            certain Node types multiple entries may be use, and so for
            that situation the pos will need to be explicitly specified,
            increment for each time that the exact value may be
            generated through the execution of the rule description for
            a given Node.
        """

        self.attr = attr
        self.value = value
        self.pos = pos

    def resolve(self, walk, dispatcher, node, value):
        if isinstance(value, Node):
            return walk(dispatcher, value, dispatcher[value])
        else:
            return dispatcher(self)(self, dispatcher, node, value)

    def __call__(self, walk, dispatcher, node):
        """
        Arguments

        walk
            the walk function
        dispatcher
            a prettyprint.Dispatcher instance.
        node
            a Node instance.
        """

        raise NotImplementedError


class Deferred(Rule):
    """
    These are special in the sense that they are deferred to generate
    a combination of the above, potentially based on some specific
    conditions as per the type.  These are generally used for the attr
    attribute of the Token, for its _getattr

    The constructor is specific to the definition.
    """

    def __call__(self, dispatcher, node):
        """
        Arguments

        dispatcher
            a walker.Dispatcher instance.
        node
            a Node instance.
        """

        raise NotImplementedError


class Space(Layout):
    """
    Represents a space.
    """


class OptionalSpace(Layout):
    """
    Represents optional space character.
    """


class Newline(Layout):
    """
    Represents a newline character.
    """


class OptionalNewline(Layout):
    """
    Represents an optional newline character.
    """


class Indent(Layout):
    """
    Represents an increment to the indentation level.
    """


class Dedent(Layout):
    """
    Represents an decrement to the indentation level.
    """


class PushScope(Layout):
    """
    Push in a new scope
    """


class PopScope(Layout):
    """
    Pops out a scope.
    """


class Attr(Token):
    """
    Return the value as specified in the attribute
    """

    def _getattr(self, dispatcher, node):
        if isinstance(self.attr, Deferred):
            return self.attr(dispatcher, node)
        else:
            return getattr(node, self.attr)

    def __call__(self, walk, dispatcher, node):
        value = self._getattr(dispatcher, node)
        if is_empty(value):
            return
        for chunk in self.resolve(
                walk, dispatcher, node, value):
            yield chunk


class Text(Token):
    """
    Simply leverage the dispatcher object for generating the rendering
    of the value required.
    """

    def __call__(self, walk, dispatcher, node):
        for chunk in self.resolve(walk, dispatcher, node, self.value):
            yield chunk


class JoinAttr(Attr):
    """
    Join the attr with value.
    """

    def __call__(self, walk, dispatcher, node):
        nodes = iter(self._getattr(dispatcher, node))

        try:
            target_node = next(nodes)
        except StopIteration:
            return

        for chunk in self.resolve(walk, dispatcher, node, target_node):
            yield chunk

        for target_node in nodes:
            # note that self.value is to be defined in the definition
            # format also.
            for value_node in walk(dispatcher, node, self.value):
                yield value_node
            for chunk in self.resolve(walk, dispatcher, node, target_node):
                yield chunk


class ElisionToken(Attr, Text):
    """
    The special snowflake token just for Elision, simply because of how
    the ES5 specification (ECMA-262), section 11.1.4, specifies how the
    production of Elision is to be done.  The value is to be captured as
    an integer and is then later used by whatever processing required.

    While the name of this class is very specific, the meaning of the
    arguments for the constructor will remain the same.  The `attr` be
    the attribute to extract from the token, with the value being
    handled similar to the Text interpretation of value.
    """

    def __call__(self, walk, dispatcher, node):
        value = self._getattr(dispatcher, node)
        for chunk in self.resolve(
                walk, dispatcher, node, self.value * value):
            yield chunk


class ElisionJoinAttr(ElisionToken):
    """
    The Elision type does require a bit of special handling, given that
    particular Node type also serve the function of the joiner.

    Note that the ',' token will always be automatically yielded.
    """

    def __call__(self, walk, dispatcher, node):
        nodes = iter(self._getattr(dispatcher, node))

        try:
            previous_node = next(nodes)
        except StopIteration:
            return

        for chunk in self.resolve(walk, dispatcher, node, previous_node):
            yield chunk

        for next_node in nodes:
            # note that self.value is to be defined in the definition
            # format also.
            if not isinstance(previous_node, Elision):
                # TODO find a better way to deal with this magic string
                # using next_node to avoid using the Array which may
                # provide a misleading position
                yield next(walk(dispatcher, next_node, (Text(value=','),)))

            if not isinstance(next_node, Elision):
                for value_node in walk(dispatcher, node, self.value):
                    yield value_node
            for chunk in self.resolve(walk, dispatcher, node, next_node):
                yield chunk
            previous_node = next_node


class Optional(Token):
    """
    Optional text, depending on the node having an attribute

    attr
        the attr that is required for the statement to execute
    value
        the token definition segment to be executed
    """

    def __call__(self, walk, dispatcher, node):
        if is_empty(getattr(node, self.attr)):
            return

        # note that self.value is to be defined in the definition
        # format also.
        for chunk in walk(dispatcher, node, self.value):
            yield chunk


class Operator(Attr):
    """
    An operator symbol.
    """

    # TODO figure out how to yield it in a way that tags this as an
    # operator, so that it can be properly normalized by the dispatcher base
    # tracker class. (i.e. no space before ':' but after, no space
    # between + iff not followed by unary +/++)

    def _getattr(self, dispatcher, node):
        if self.attr:
            return getattr(node, self.attr)
        else:
            return self.value


class Iter(Deferred):
    """
    Produces an iterator for the Attr.
    """

    def __call__(self, dispatcher, node):
        return iter(node)


class Declare(Deferred):
    """
    Record the declaration of the specific identifier.
    """

    def __init__(self, attr):
        self.attr = attr

    def _handle(self, handler, parent, child, idx=None):
        if not isinstance(child, Identifier):
            raise TypeError(
                "in %r, the resolved attribute '%s%s' is not an Identifier" %
                (parent, self.attr, '' if idx is None else '[%d]' % idx)
            )
        # invoke it with the specific method signature for Deferred
        # handlers.
        handler(child)

    def __call__(self, dispatcher, node):
        target = getattr(node, self.attr)

        if is_empty(target):
            # can't record nothing.
            return target

        # look up the layout handler for this deferred type
        handler = dispatcher(self)
        if handler is not NotImplemented:
            handler = partial(handler, dispatcher)
            if isinstance(target, list):
                for idx, item in enumerate(target):
                    self._handle(handler, node, item, idx)
            else:
                self._handle(handler, node, target)

        # finally, return the actual attribute
        return target


class Resolve(Deferred):
    """
    Resolve an identifier.  Naturally, this is used by the Identifier
    asttype to look up previously declared names.
    """

    def __call__(self, dispatcher, node):
        if not isinstance(node, Identifier):
            raise TypeError("the Resolve deferred only works with Identifier")

        handler = dispatcher(self)
        if handler is not NotImplemented:
            # the handler will return the value
            return handler(dispatcher, node)
        return node.value


children_newline = JoinAttr(Iter(), value=(Newline,))
children_comma = JoinAttr(Iter(), value=(Text(value=','), Space,))
