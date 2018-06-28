# linkedin2GoPhish

this script allow you to craft email addresses from linkedin organization research. This is widely inspired from [linkedin2username](https://github.com/initstring/linkedin2username)

This is a pure web-scraper, no API key required. You use your valid LinkedIn username and password to login, it will create several lists of emails for all employees of a company you point it at, based on the format you give hime (firstname.lastnam@domaine, f.lastname@domain, etc).


## installation

this script is only python3 compatible (any backward compatibility pull request is welcome)
use venv

```
git clone https://github.com/gfrancqu/linkedin2GoPhish
virtualenv -p python3 venv
source venv/bin/activate
pip install -r requirements.txt
```

## usage

```
usage: linkedin2GoPhish.py [-h] [-p PASSWORD] [-n DOMAIN] [-d DEPTH]
                            [-s SLEEP] [-f FORMAT] [-u URL] [-k APIKEY]
                            username company

positional arguments:
  username              A valid LinkedIn username.
  company               Company name.

optional arguments:
  -h, --help            show this help message and exit
  -p PASSWORD, --password PASSWORD
                        Specify your password on in clear-text on the command
                        line. If not specified, will prompt and not display on
                        screen.
  -n DOMAIN, --domain DOMAIN
                        The domain name to add to the email addresses. default
                        is [company].com [example: "-n uber.com" would ouput
                        jschmoe@uber.com]
  -d DEPTH, --depth DEPTH
                        Search depth. If unset, will try to grab them all.
  -s SLEEP, --sleep SLEEP
                        Seconds to sleep between pages. defaults to 3.
  -f FORMAT, --format FORMAT
                        Format for the email address, 1:first.last@domain,
                        2:f.last@domain, 3:flast@domain. Default is
                        flast@domain
  -u URL, --url URL     Host for the goPhish API
  -k APIKEY, --apikey APIKEY
                        API key for the goPhish API
```

## sample usage
this command will get the first result page of the amazon employees and format their email addresse with the format firstname.lastname@amazon.fr
```
(venv) guy@kali:~/linkedin2GoPhish# python link2GoPhish.py -f 1 -d 1 -n amazon.fr francqueville.g@gmail.com amazon
```

output is available in link2gophis-output/amazon.csv, this out file can be imported into gophish but you can ask the script to automatically create a group into your [gophish](https://getgophish.com/) instance by specifying the --url parameter with the addresse of your gophish admin server and the --apikey parameter (you can find it under the "settings" tabs of gophish)

```
(venv) guy@kali:~/linkedin2GoPhish# python link2GoPhish.py -f 1 -d 1 -n amazon.fr francqueville.g@gmail.com amazon --url https://127.0.0.1:3333 --apikey abcdefghijklmnopqrst123
```

this will automatically create a user group "l2gp - [company]" in your gophish server 


## develop

feel free to improve the script with new functionnality, email format, etc ! pull requests are welcome