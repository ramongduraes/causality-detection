import logging
import grpc
import service
import concurrent.futures as futures
import sys
import os
from urllib.error import HTTPError
from multiprocessing import Pool

import service.service_spec.causality_detection_pb2_grpc as grpc_bt_grpc
from service.service_spec.causality_detection_pb2 import Result

from .granger_causality import granger_causality
import pandas as pd
import numpy as np
import io

logging.basicConfig(
    level=10, format="%(asctime)s - [%(levelname)8s] - %(name)s - %(message)s"
)
log = logging.getLogger("causality_detection_service")


def _detect_causality(request):
    log.debug('Detecting causality')
    # Python command call arguments. Key = argument name, value = tuple(type, required?, default_value)

    try:
        data = pd.read_csv(io.StringIO(request.data))
        lags = request.lags if request.lags != 0 else 3
        modelling_type = request.modelling_type if request.modelling_type != "" else "trend"
        start = int(request.start) if request.start != "" else 0
        end = int(request.end) if request.end != "" else data.shape[0]
        input_features = request.input_features.split(',') if request.input_features != "" else data.columns[0:-1]
        output_feature = request.output_feature if request.output_feature != "" else data.columns[-1]

    except Exception as e:
        log.debug('Error treating input.')
        log.error(str(e))
        raise e

    try:
        all_features = input_features.append(output_feature)
        selected_data = data
        selected_data = selected_data.loc[start:end, all_features]
        selected_data.dropna(inplace=True)
        output = granger_causality(selected_data, input_features, output_feature, lags=lags, our_type=modelling_type)
        return output
    except Exception as e:
        log.debug('Error calling granger_causality.')
        log.error(str(e))
        raise e


class CausalityDetectionServicer(grpc_bt_grpc.CausalityDetectionServicer):
    """Causality detection servicer class to be added to the gRPC stub.
    Derived from protobuf (auto-generated) class."""

    def __init__(self):
        log.debug("CausalityDetectionServicer created!")

        self.result = Result()

        self.root_path = os.getcwd()
        self.input_dir = self.root_path + "/service/temp/input"
        service.initialize_diretories([self.input_dir])

    def detect_causality(self, request, context):
        """Evaluates causality using time series"""
        log.debug("Received request")
        with Pool(1) as p:
            try:
                output = p.apply(_detect_causality, (request,))
                log.debug("Returning on service complete!")
                self.result.response = output
                return self.result
            except Exception as e:
                log.error(e)
                self.result.response = e
                return self.result


def serve(max_workers=5, port=7777):
    """The gRPC serve function.

    Params:
    max_workers: pool of threads to execute calls asynchronously
    port: gRPC server port

    Add all your classes to the server here.
    (from generated .py files by protobuf compiler)"""

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers))
    grpc_bt_grpc.add_CausalityDetectionServicer_to_server(
        CausalityDetectionServicer(), server)
    server.add_insecure_port('[::]:{}'.format(port))
    log.debug("Returning server!")
    return server


if __name__ == '__main__':
    """Runs the gRPC server to communicate with the Snet Daemon."""
    parser = service.common_parser(__file__)
    args = parser.parse_args(sys.argv[1:])
    service.serviceUtils.main_loop(serve, args)