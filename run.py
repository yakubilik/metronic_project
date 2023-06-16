import sys
import docker

image_name = "t-shirt_app:latest"
client = docker.from_env()

# Check if the image already exists
existing_images = client.images.list()
image_exists = any(image_name in image.tags for image in existing_images)

if image_exists:
    # Run a container using the existing image
    container = client.containers.run(image_name, ports={'5005/tcp': 5005}, remove=True)
    # Get container logs
else:
    # Build a new image
    dockerfile_path = "./"
    image, build_logs = client.images.build(path=dockerfile_path, tag=image_name)
    # Get build logs
    # Run a container using the newly built image
    container = client.containers.run(image_name, ports={'5005/tcp': 5005}, remove=True)
    # Get container logs