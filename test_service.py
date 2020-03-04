import grpc

# import the generated classes
import service.service_spec.causality_detection_pb2_grpc as grpc_bt_grpc
import service.service_spec.causality_detection_pb2 as grpc_bt_pb2

from service import registry, base64_to_jpg, clear_file

if __name__ == "__main__":

    try:
        # open a gRPC channel
        endpoint = "localhost:{}".format(registry["causality_detection_service"]["grpc"])
        channel = grpc.insecure_channel("{}".format(endpoint))
        print("Opened channel")

        # setting parameters
        grpc_method = "increase_image_resolution"
        input_image = \
            "https://www.gettyimages.ie/gi-resources/images/Homepage/Hero/UK/CMS_Creative_164657191_Kingfisher.jpg"
        model = "proSR"
        scale = 5

        # create a stub (client)
        stub = grpc_bt_grpc.CausalityDetectionStub(channel)
        print("Stub created.")

        # create a valid request message
        request = grpc_bt_pb2.CausalityDetectionRequest(input=input_image,
                                                        model=model,
                                                        scale=scale)
        # make the call
        response = stub.increase_image_resolution(request)
        print("Response received!")

        # et voilà
        output_file_path = "./causality_detection_test_output.jpg"
        if response.data:
            base64_to_jpg(response.data, output_file_path)
            clear_file(output_file_path)
            print("Service completed!")
        else:
            print("Service failed! No data received.")
            exit(1)

    except Exception as e:
        print(e)
        exit(1)
