# I don't know if it's working, but who has MacOS or Linux, please check it out, thanks.
FluxarPath="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && cd ../../../.. && pwd )"
echo 'export PATH="$FluxarPath:$PATH"' >> ~/.bashrc
chmod +x set_path.sh
