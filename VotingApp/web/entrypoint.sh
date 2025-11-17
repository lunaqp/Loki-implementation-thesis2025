#!/bin/sh
# Replace env variables in the nginx template
echo ${VITE_API_VOTINGAPP}
envsubst '${VITE_API_VOTINGAPP}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Start nginx in foreground
nginx -g 'daemon off;'
