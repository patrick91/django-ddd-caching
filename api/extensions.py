import time
from datetime import datetime
from inspect import isawaitable
import base64


from google.protobuf import timestamp_pb2
from strawberry.extensions import Extension
from strawberry.extensions.tracing.utils import should_skip_tracing
from strawberry.types.execution import ExecutionContext

from . import apollo_reports_pb2


def timestamp_to_proto(ts: int) -> timestamp_pb2.Timestamp:
    timestamp = timestamp_pb2.Timestamp()
    timestamp.FromNanoseconds(nanos=ts)

    return timestamp


def path_to_string(path) -> str:
    if path is None:
        return ""

    return ".".join((str(part) for part in path.as_list()))


class ApolloTracingExtension(Extension):
    def __init__(self):
        self.trace = apollo_reports_pb2.Trace()
        self.root_node = apollo_reports_pb2.Trace.Node()  # type: ignore

        self.nodes = {"": self.root_node}

    def on_request_start(self, *, execution_context: ExecutionContext):
        self.trace.start_time.MergeFrom(timestamp_to_proto(self.now()))
        self.root_node.start_time = self.now()

        self.start_timestamp = self.now()

    def on_request_end(self, *, execution_context: ExecutionContext):
        self.trace.duration_ns = self.now() - self.start_timestamp
        self.trace.end_time.MergeFrom(timestamp_to_proto(self.now()))
        self.root_node.end_time = self.now()

        self.end_time = datetime.utcnow()

    def on_parsing_start(self):
        self._start_parsing = self.now()

    def on_parsing_end(self):
        self._end_parsing = self.now()

    def on_validation_start(self):
        self._start_validation = self.now()

    def on_validation_end(self):
        self._end_validation = self.now()

    def now(self) -> int:
        return time.perf_counter_ns()

    def get_results(self):
        self.trace.root.MergeFrom(self.root_node)

        return {
            "ftv1": base64.encodebytes(self.trace.SerializeToString()).decode("utf-8")
        }

    def ensure_parent_node(self, path):
        parent_path = path_to_string(path.prev)
        parent_node = self.nodes.get(parent_path)

        if parent_node:
            return parent_node

        return self.new_node(path.prev)

    def new_node(self, path):
        parent_node = self.ensure_parent_node(path)
        node = parent_node.child.add()

        if type(path.key) == int:
            node.index = path.key
        else:
            node.response_name = path.key

        self.nodes[path_to_string(path)] = node

        return node

    async def resolve(self, _next, root, info, *args, **kwargs):
        if should_skip_tracing(_next, info):
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result  # pragma: no cover

            return result

        node = self.new_node(info.path)
        node.type = str(info.return_type)
        node.parent_type = str(info.parent_type)
        node.start_time = self.now() - self.start_timestamp

        if type(info.path.key) == str and info.path.key != info.field_name:
            node.original_field_name = info.field_name

        try:
            result = _next(root, info, *args, **kwargs)

            if isawaitable(result):
                result = await result

            return result
        finally:
            node.end_time = self.now() - self.start_timestamp
