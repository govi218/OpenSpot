#!/bin/bash

set -e
heroku container:login 
heroku container:push -R web --app open-spot
heroku container:release web --app open-spot

exit 0
