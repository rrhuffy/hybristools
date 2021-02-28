Installing hybristools
==
I'm using these scripts on a daily basis using either Linux in VM or WSL in Windows. 
They will also work in Windows (without WSL), but without convenient shortcuts (yet).

<!--ts-->
   * [Installing hybristools](#installing-hybristools)
   * [Linux](#linux)
   * [Windows](#windows)
   * [Shared settings and arguments](#shared-settings-and-arguments)
      * [Selecting server and credentials](#selecting-server-and-credentials)
      * [Using proxy](#using-proxy)
      * [Using servers with basic http auth](#using-servers-with-basic-http-auth)
      * [Debugging](#debugging)

<!-- Added by: rafal, at: Mon Mar  1 17:45:57 CET 2021 -->

<!--te-->
<!-- ~/gh-md-toc --no-backup $PROJECTS_DIR/hybristools/INSTALL.md -->

Linux
==
Check if you have installed Python 3.6 or higher by executing `python3 -V`.<br/>
Optionally you can use venv to have all dependencies installed in a separated folder.
Otherwise, all dependencies will be installed globally.
```shell
python3 -m venv venv
source venv/bin/activate
```
Install dependencies:
```shell
python3 -m pip install --upgrade pip
python3 -m pip install wheel
python3 -m pip install -r requirements.txt
```

This project uses multiple bash functions stored in `bashrc` file and require that `PROJECTS_DIR` environment variable is set to  folder which contains this repository.<br/>
Add lines below to your `~/.bashrc`:
```shell
export PROJECTS_DIR=/path/to/folder/which/contains/this/repository
source $PROJECTS_DIR/hybristools/bashrc
```
Then either restart your terminal or type `source ~/.bashrc` to load changes into your current terminal. From this point all new terminals will work without any additional work.

Now to test if everything is working you can execute Hello World in groovy on localhost server by:
```shell
xg 'println "Hello world!"'
```
And check number of orders:
```shell
xf "select count(*) from {Order}"
```

Windows
==

Check if you have installed Python 3.6 or higher by executing `python -V` or `python3 -V`.<br/>

Optionally you can use venv to have all dependencies installed in a separated folder.
Otherwise, all dependencies will be installed globally.
```shell
python -m venv venv
venv\Scripts\activate.bat
```
Install dependencies:
```shell
python -m pip install --upgrade pip
python -m pip install wheel
python -m pip install -r requirements.txt
```

Set permanent environment variables:
```shell
setx HYBRIS_HAC_URL https://localhost:9002/hac
setx HYBRIS_USER admin
setx HYBRIS_PASSWORD nimda
```
Restart cmd.exe to start using newly set environment variables and execute:
```shell
cd C:\path\to\hybristools
# if you didn't use venv
python src\execute_script.py "println 'Hello World!'" groovy
python src\execute_flexible_search.py "select count(*) from {Order}"
python src\execute_flexible_search.py flexible\ShowItemDirect --parameters=Media
# or if you used venv then you need to provide python executable from virtual environment
C:\Projects\hybristools\venv\Scripts\python.exe C:\Projects\hybristools\src\execute_script.py "println 'Hello World!'" groovy
C:\Projects\hybristools\venv\Scripts\python.exe C:\Projects\hybristools\src\execute_flexible_search.py "select count(*) from {Order}"
C:\Projects\hybristools\venv\Scripts\python.exe C:\Projects\hybristools\src\execute_flexible_search.py flexible\ShowItemDirect --parameters=Media
```
TODO: shortcuts using `DOSKEY` and changing environment variables by `SET`, for example:
```shell
# global version
doskey xg=python C:\Projects\hybristools\src\execute_script.py $* groovy
# venv version
doskey xg=C:\Projects\hybristools\venv\Scripts\python.exe C:\Projects\hybristools\src\execute_script.py $* groovy
# and now just execute:
xg "println 'Hello World!'"

# to change servers you can use shortcuts below
doskey setlocal=set HYBRIS_HAC_URL=https://localhost:9002/$T set HYBRIS_USER=admin$T set HYBRIS_PASSWORD=nimda
doskey setpowertools=set HYBRIS_HAC_URL=https://powertools:9002/hac$T set HYBRIS_USER=admin$T set HYBRIS_PASSWORD=nimda
```
To have them loaded automatically you can install `ConEmu` and add them to `Settings` -> `Startup` -> `Environment`.

Shared settings and arguments
==

## Selecting server and credentials

Most scripts uses hybris_requests_helper.py library, because of that they share two ways of selecting server URL and credentials:

1. By using arguments passed to script: 

```shell
xg "println 'Hello World!'" --address=https://localhost:9002/hac --user=admin --password=nimda
```

2. By using environment variables:
```shell
# bashrc define and use these variables
# if they are not set, they will have default values assigned
export HYBRIS_HAC_URL=${HYBRIS_HAC_URL:-https://localhost:9002/hac}
export HYBRIS_USER=${HYBRIS_USER:-admin}
export HYBRIS_PASSWORD=${HYBRIS_PASSWORD:-nimda}
# now just run script
xg "println 'Hello World!'"
```
Warning! Using credentials in arguments will leave them visible in history.
Using environment variables is a bit better, but it's also not fully secure.
Because of that, you can use empty user/password and that will be fetched based on `HYBRIS_HAC_URL`
from `keepass` if you have `KeePassHttp` plugin paired with library `keepasshttplib`.

You can create a function for assigning variables for specific servers like:
```shell
setlocal() { 
    export HYBRIS_HAC_URL="https://localhost:9002/hac"
    export HYBRIS_USER="admin"
    export HYBRIS_PASSWORD="nimda"
}
setpowertools() {
    export HYBRIS_HAC_URL="https://powertools:9002/hac"
    export HYBRIS_USER="admin"
    export HYBRIS_PASSWORD="nimda"
}
# user and password are empty, so they will be fetched from keepass
setprojectxproduction() {
    export HYBRIS_HAC_URL="https://projectxproduction:9002/hac"
    export HYBRIS_USER=""
    export HYBRIS_PASSWORD=""
}
# then to check amount of orders in all servers you'll need to:
setlocal
xf "select count(*) from {Order}"
setpowertools
xf "select count(*) from {Order}"
setprojectxproduction
xf "select count(*) from {Order}"
```

If you constantly change servers I strongly suggest adding `HYBRIS_HAC_URL` to your `PS1` to constantly see selected server:
```shell
# normal prompt
user@host:~$

# just add at beginning
export PS1='<$HYBRIS_HAC_URL> '$PS1
<https://localhost:9002/hac> user@host:~$

# version with removed protocol, port and hac suffix to remove noise
export PS1='<$(echo $HYBRIS_HAC_URL|sed -E "s|https?://||;s|(:9002)?(/hac)?\$||")> '$PS1
<localhost> user@host:~$ setpowertools
<powertools> user@host:~$ setlocal
<localhost> user@host:~$

# if you want that in all your shells then put "export PS1=..." at end of your ~/.bashrc
```

## Using proxy
To use proxy just set `HTTP_PROXY` or `HTTPS_PROXY` environment variable

## Using servers with basic http auth
If you have a server behind proxy with basic http authorization then put your basic auth credentials into URL using `user:password@server`:
```shell
export HYBRIS_HAC_URL=https://basicHttpAuthUser:basicHttpAuthPassword@server/hac
```

## Debugging

Some scripts execute pdb when uncaught exception occur. In this case you can print values to troubleshoot a problem. Use `u`/`d` to jump up/down in a stacktrace.

execute_script.py and multiline_tabulate.py uses logging_helper.py which gives `-v` and `-q` arguments.
If you use verbose switch twice (`-vv`) it will launch pysnooper which prints executed code with all variable assignments. Adding another `v` will increase its depth.
