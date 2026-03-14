FROM public.ecr.aws/x8v8d7g8/mars-base:latest

WORKDIR /app

ENV NODE_ENV=development

# Copy the ts-pattern-verify app
COPY ts-pattern-verify/package.json ts-pattern-verify/package-lock.json ./
RUN npm ci --include=dev --no-audit --no-fund

COPY ts-pattern-verify/ .

# Copy patches to root for golden_solution.py access
COPY solution.patch /solution.patch
COPY test.patch /test.patch

# Configure git and apply the test patch (adds the new test file)
RUN git config --global user.email "test@example.com" && \
    git config --global user.name "Test" && \
    git init && git add -A && git commit -m "init" && \
    git apply --whitespace=nowarn /test.patch || true

CMD ["/bin/bash"]
