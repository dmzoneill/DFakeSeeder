# Stage 1: Build Environment
FROM fedora:40

# Install necessary packages and clean up in the same layer
# hadolint ignore=DL3041
RUN dnf update -y && \
    dnf install -y \
        python3 \
        python3-pip \
        python3-gobject \
        gtk4 \
        xauth \
        mesa-libGL \
        mesa-dri-drivers \
        which && \
    dnf clean all

# Set user and group IDs
ARG USER_ID=1000
ARG GROUP_ID=1000
ARG USER_NAME=dfakeseeder

# Create user and group with -l flag to avoid large image issue
RUN groupadd -g ${GROUP_ID} ${USER_NAME} && \
    useradd -l -m -u ${USER_ID} -g ${GROUP_ID} -s /bin/bash ${USER_NAME}

# Set working directory
WORKDIR /app

# Copy dependency files
COPY Pipfile Pipfile.lock /app/

# Create necessary directories, set permissions, and change ownership in one layer
RUN mkdir -vp /run/user/${USER_ID}/at-spi /home/${USER_NAME}/.cache /home/${USER_NAME}/.config && \
    chown -R ${USER_NAME}:${USER_NAME} /app /run/user/${USER_ID} /home/${USER_NAME}/.cache /home/${USER_NAME}/.config

# Switch to the created user
USER ${USER_NAME}

# Set environment variables
ENV XDG_RUNTIME_DIR=/run/user/${USER_ID}
ENV LIBGL_ALWAYS_SOFTWARE=1
ENV PATH="/home/${USER_NAME}/.local/bin:${PATH}"

# Install pipenv and dependencies in one layer using --no-cache-dir
# hadolint ignore=DL3013
RUN pip3 install --no-cache-dir --no-warn-script-location pipenv && \
    pipenv install --system --deploy

# Switch to root to create symlink
USER 0
RUN ln -s /home/dfakeseeder/.local/bin/py.test /usr/bin/pytest

# Switch back to the created user
USER ${USER_NAME}

# Copy application code
COPY . /app

# Set display environment variable
ENV DISPLAY=:0
ENV GTK_THEME=Adwaita:dark

# Set Python path
ENV PYTHONPATH="/usr/lib/python3/dist-packages"

# Mount host's GTK theme configuration directory into the container
VOLUME /usr/share/themes
VOLUME /tmp/.X11-unix

# Set entrypoint command
WORKDIR /app/d_fake_seeder
CMD ["python3", "dfakeseeder.py"]
