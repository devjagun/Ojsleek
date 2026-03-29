FROM public.ecr.aws/x8v8d7g8/mars-base:latest
WORKDIR /app
COPY package.json ./
RUN NODE_ENV=development npm install --ignore-scripts --legacy-peer-deps
COPY . .
CMD ["/bin/bash"]
