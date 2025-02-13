# Copyright (c) 2021-2022, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import inspect
import typing
from abc import abstractmethod

import neo
import typing_utils

from morpheus.config import Config
from morpheus.config import CppConfig
from morpheus.messages import MultiInferenceMessage
from morpheus.messages import MultiMessage
from morpheus.pipeline.multi_message_stage import MultiMessageStage
from morpheus.pipeline.stream_pair import StreamPair


class PreprocessBaseStage(MultiMessageStage):
    """
    This is a base pre-processing class holding general functionality for all preprocessing stages.

    Parameters
    ----------
    c : `morpheus.config.Config`
        Pipeline configuration instance.

    """

    def __init__(self, c: Config):
        super().__init__(c)

        self._should_log_timestamps = True

    def accepted_types(self) -> typing.Tuple:
        """
        Returns accepted input types for this stage.

        """
        return (MultiMessage, )

    @abstractmethod
    def _get_preprocess_fn(self) -> typing.Callable[[MultiMessage], MultiInferenceMessage]:
        pass

    @abstractmethod
    def _get_preprocess_node(self, seg: neo.Segment):
        pass

    def _build_single(self, seg: neo.Segment, input_stream: StreamPair) -> StreamPair:

        stream = input_stream[0]
        out_type = MultiInferenceMessage

        preprocess_fn = self._get_preprocess_fn()

        preproc_sig = inspect.signature(preprocess_fn)

        # If the innerfunction returns a type annotation, update the output type
        if (preproc_sig.return_annotation and typing_utils.issubtype(preproc_sig.return_annotation, out_type)):
            out_type = preproc_sig.return_annotation

        if CppConfig.get_should_use_cpp():
            stream = self._get_preprocess_node(seg)
        else:
            stream = seg.make_node(self.unique_name, preprocess_fn)

        seg.make_edge(input_stream[0], stream)

        return stream, out_type
