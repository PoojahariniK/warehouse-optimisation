FROM node:20-alpine AS builder

WORKDIR /app

# copy manifest files (package.json, optionally package-lock.json)
COPY package*.json ./
# install dependencies (no lockfile present, so use npm install)
RUN npm install   # install all deps, including dev for build step

# copy the source tree (frontend folder is the build context)
COPY . .

# The project’s package.json defines a placeholder build script that only echoes.
# We create a dummy build output directory from the public assets so Nginx can serve it.
RUN mkdir -p build && cp -R public/* build/

FROM nginx:stable-alpine

RUN rm -rf /usr/share/nginx/html/*

# copy the generated static files into Nginx
COPY --from=builder /app/build /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
