FROM ghcr.io/ad-sdl/madsci

LABEL org.opencontainers.image.source=https://github.com/AD-SDL/camera_module
LABEL org.opencontainers.image.description="A module that implements a simple camera snapshot action"
LABEL org.opencontainers.image.licenses=MIT

#########################################
# Module specific logic goes below here #
#########################################

RUN apt-get update && \
    apt-get install -y libzbar0 && \
    rm -rf /var/lib/apt/lists/* && rm -rf /var/cache/apt/archives/*

RUN mkdir -p camera_module

COPY ./src camera_module/src
COPY ./README.md camera_module/README.md
COPY ./pyproject.toml camera_module/pyproject.toml

RUN --mount=type=cache,target=/root/.cache \
    pip install -e ./camera_module

CMD ["python", "-m", "camera_rest_node"]

# Add user to video group to access camera
RUN usermod -a -G video madsci

#########################################
