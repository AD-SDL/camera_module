FROM ghcr.io/ad-sdl/wei

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/camera_module
LABEL org.opencontainers.image.description="A module that implements a simple camera snapshot action"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN mkdir -p camera_module

COPY ./src camera_module/src
COPY ./README.md camera_module/README.md
COPY ./pyproject.toml camera_module/pyproject.toml
COPY ./tests camera_module/tests

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./camera_module

CMD ["python", "camera_module/src/camera_rest_node.py"]

# Add user to video group to access camera
RUN usermod -a -G video app

#########################################
