# Keep Docker client proxy configuration out of build steps and containers.
proxy_build_args=()
proxy_run_args=()
for proxy in HTTP_PROXY HTTPS_PROXY FTP_PROXY ALL_PROXY NO_PROXY \
             http_proxy https_proxy ftp_proxy all_proxy no_proxy; do
    proxy_build_args+=(--build-arg "$proxy=")
    proxy_run_args+=(--env "$proxy=")
done
