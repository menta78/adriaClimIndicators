#!/usr/bin/env bash


## Copyright 2022 CMCC
##
## This program is free software: you can redistribute it and/or modify it under
## the terms of the GNU General Public License as published by the Free Software
## Foundation, either version 3 of the License, or (at your option) any later
## version.
## This program is distributed in the hope that it will be useful, but WITHOUT
## ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
## FOR A PARTICULAR PURPOSE. See the GNU General Public License for more
## details.
## You should have received a copy of the GNU General Public License along with
## this program. If not, see <https://www.gnu.org/licenses/>.


## Bash settings ###############################################################

set -o errexit
set -o errtrace
set -o nounset
set -o pipefail

## Variables ###################################################################

declare curl="curl"
declare wget="wget"
declare find="find"

## Param passed to wget for -P (directory prefix): the target dir where to save
## the subdirs and files.
declare dir_prefix="."

declare erddap_domain="https://erddap.cmcc-opa.eu"
declare erddap_url="${erddap_domain}/erddap"

declare erddap_username=""

declare erddap_password=""

declare erddap_dataset_glob=""

declare erddap_regex=".*"

declare USAGE=""
USAGE=$(cat <<-END

Usage
------
./erddap-downloader.sh -u <USERNAME> -p <PASSWORD> -d <DATASET_PATH>


Optional params
----------------
  -e <ERDDAP_URL> (default: $erddap_url)
  -r <ERDDAP_REGEX> Regexp for filtering subpaths and filenames (default: $erddap_regex)
  -t <DST_DIR> Dest dir (default: $dir_prefix)
  -h This help


Example
--------
Suppose we want to download some datasets from the ERDDAP node

  https://erddap.cmcc-opa.eu/erddap/

and we have identified the following files for downloading:

  https://erddap.cmcc-opa.eu/erddap/files/wrfhydro_historical_2aff_7940_c642/1992/

The command would be:

  ./erddap-downloader.sh -u <USERNAME> -p <PASSWORD> -d "wrfhydro_historical_2aff_7940_c642/1992"


Notes
------
Please consider that ERDDAP_REGEX must also take into account the path, not only
the filename.

Note also that during the job some index.html files are downloaded: they are
removed at the end of the job.

END
     )

## Command-line options ########################################################

declare opt=""
while getopts ":e:u:p:d:r:t:h" opt; do
    case "$opt" in
        e)
            erddap_url="$OPTARG"
            ;;
        u)
            erddap_username="$OPTARG"
            ;;
        p)
            erddap_password="$OPTARG"
            ;;
        d)
            erddap_dataset_glob="$OPTARG"
            ;;
        r)
            erddap_regex="$OPTARG"
            ;;
        t)
            dir_prefix="$OPTARG"
            ;;
        h)
            echo "$USAGE"
            exit 0
            ;;
        :)
            echo "Option -$OPTARG requires an argument"
            exit 1
            ;;
    esac
done

## Functions ###################################################################

function get_session_id()
{
    $curl -c- -s \
         "${erddap_url}/login.html" \
         -X POST \
         -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8' \
         -H 'Accept-Language: en,it;q=0.7,en-US;q=0.3' \
         -H 'Accept-Encoding: gzip, deflate, br' \
         -H 'Content-Type: application/x-www-form-urlencoded' \
         -H 'Connection: keep-alive' \
         -H 'Cookie: JSESSIONID=ADEDA906F1BD6625567B160EBA98ADED' \
         -H 'Upgrade-Insecure-Requests: 1' \
         -H 'Sec-Fetch-Dest: document' \
         -H 'Sec-Fetch-Mode: navigate' \
         -H 'Sec-Fetch-Site: same-origin' \
         -H 'Sec-Fetch-User: ?1' \
         -H 'Pragma: no-cache' \
         -H 'Cache-Control: no-cache' \
         --data "user=${erddap_username}&password=${erddap_password}" \
        | grep JSESSIONID | cut -f7
}

function download_files()
{
    declare JSESSIONID="$1"

    $wget --no-parent -r --level=inf -nv \
          -P "$dir_prefix" \
          -e robots=off \
          --accept-regex "$erddap_regex" \
          --header='Connection: keep-alive' \
          --header="Cookie: JSESSIONID=${JSESSIONID}" \
          --header='Upgrade-Insecure-Requests: 1' \
          --header='Sec-Fetch-Dest: document' \
          --header='Sec-Fetch-Mode: navigate' \
          --header='Sec-Fetch-Site: same-origin' \
          --header='Sec-Fetch-User: ?1' \
          --header='Pragma: no-cache' \
          --header='Cache-Control: no-cache' \
          "${erddap_url}/files/${erddap_dataset_glob}"
}

function remove_index_html()
{
    $find "$dir_prefix" -name 'index.html*' -delete
}

## Main ########################################################################

[ "$#" -eq "0" ] && {
    echo "$USAGE"
    exit 0
}

[ -n "$dir_prefix" ] || {
    echo "Empty dir prefix"
    exit 1
}

[ -n "$erddap_url" ] || {
    echo "Empty ERDDAP URL"
    exit 1
}

[ -n "$erddap_username" ] || {
    echo "Empty ERDDAP username"
    exit 1
}

[ -n "$erddap_password" ] || {
    echo "Empty ERDDAP password"
    exit 1
}

[ -n "$erddap_dataset_glob" ] || {
    echo "Empty ERDDAP path"
    exit 1
}

[ -n "$erddap_regex" ] || {
    echo "Empty ERDDAP regex"
    exit 1
}

command -v "$curl" >/dev/null 2>&1 || {
    echo "Cannot find 'curl'"
    exit 1
}

command -v "$wget" >/dev/null 2>&1 || {
    echo "Cannot find 'wget'"
    exit 1
}

command -v "$find" >/dev/null 2>&1 || {
    echo "Cannot find 'find'"
    exit 1
}

## Add a trailing slash if missing
[ "${erddap_dataset_glob: -1}" == "/" ] || {
    erddap_dataset_glob="$erddap_dataset_glob/"
}

download_files "$(get_session_id)" &&
    remove_index_html

exit 0
