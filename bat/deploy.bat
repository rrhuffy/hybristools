@ECHO OFF
REM Assuming hybris location in C:\Projects\ProjectX\hybris\bin
REM Assuming C:\Program Files\Git\bin\sh.exe exist
REM You need pscp.exe and plink.exe in PATH

REM Using these ENV variables here (security reasons): SSH_IP, SSH_USER, SSH_PASSWORD, HAC_USER, HAC_PASSWORD
REM you can set them permanently by executing in cmd: "setx key value"

REM Using external programs, for least dependencies you can remove things like:
REM python %PROJECTS_DIR%\Scripts\py\lib\clipboard.py - for copying text into clipboard to inform people on chat
REM Lines touching clipboard can be replaced with "ECHO text" + "PAUSE", but then script won't be fully automatic
REM CALL info/success/fail - for showing win10 toast notifications during deploy (external command)
REM UPDATE_SYSTEM_PARAMETERS - parameters for automatic updating running system after deploy
REM python %PROJECTS_DIR%\hybristools\src\update_initialize_system.py update - script for automatic updating running system after deploy

REM To avoid more dependencies, things that need interaction like writing on hipchat/flowdock have PAUSE
REM so you can write on chat and click enter to move forward

REM It is best to have output both in console (to see current status) and log that to file:
REM Example in PowerShell: deploy.bat | tee C:/deploy.log
REM For cmd you need to download some third party software and do (2>&1 means redirect both stdout and stderr):
REM deploy.bat 2>&1 | TeeLikeProgram C:\deploy.log

REM %PROJECTS_DIR%\hybristools\bat\deploy.bat 2>&1 | python %PROJECTS_DIR%\Scripts\py\pytee.py C:\deploy.log

REM http://stackoverflow.com/questions/4367930/errorlevel-inside-if
REM if using volatile/not const %var% inside IF/FOR statement we must use !var! because preprocessor is expanding %var% once and only once
SETLOCAL ENABLEDELAYEDEXPANSION

REM Make a pause after updating repo and translations but before starting local ant clean all and ant production to be able to add for example custom timing stuff?
SET PAUSE_BEFORE_ANT=0
REM Make a pause after unpacking and moving all files to correct place on server but before starting a server to be able to change for example local.properties/schema?
SET PAUSE_BEFORE_STARTING_SERVER=0
REM Make a pause after starting a server but before updates to be able to run for example cleaning orphaned types?
SET PAUSE_AFTER_STARTING_SERVER_BEFORE_UPDATES=0

REM Set update running system parameters
SET UPDATE_SYSTEM_PARAMETERS=--sleep
SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS% --separator=comma
SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS% projectstore:Content Data:no:Sample Data:no,projectcore:Content Data:no
REM SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS%,projectcustomersupportbackoffice
REM SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS%,projectbackoffice
REM SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS%,projectcockpits
REM SET UPDATE_SYSTEM_PARAMETERS=%UPDATE_SYSTEM_PARAMETERS%,projectcustomerticketingfacades

SET BRANCH=develop

python %PROJECTS_DIR%\Scripts\py\lib\clipboard.py "@all starting deploy from branch %BRANCH%"
CALL info "Deploy Status" "Inform on hipchat people about deploy start (text copied to clipboard)"

ECHO !TIME:~0,8! Cleaning up repo and getting newest develop
CALL :RunShAndQuitIfFail "cd /c/Projects/ProjectX/hybris/bin && git clean -fd && git reset --hard && git checkout %BRANCH% && git pull && git status"

REM this is custom deployment step from project, use externally provided translations from customer
ECHO !TIME:~0,8! Synchronizing translations 1 of 3: zipping translations on server
CALL :RunPlinkAndQuitIfFail "cd /home/sshUser/ && rm -f translations.zip && zip -q -r translations.zip translations"
ECHO !TIME:~0,8! Synchronizing translations 2 of 3: downloading zip
CALL :RunPscpWithCredentialsAndQuitIfFail %SSH_IP%:/home/sshUser/translations.zip C:\Projects\X\hybris\bin\custom\translations.zip
ECHO !TIME:~0,8! Synchronizing translations 3 of 3: applying zip
CALL :RunCmdAndQuitIfFail "cd /D C:\Projects\ProjectX\hybris\bin\custom && (if exist translations (rmdir /S /Q translations)) && unzip -q translations.zip && del /Q translations.zip"

IF %PAUSE_BEFORE_ANT% == 1 (
    CALL info "Deploy Status" "Now add custom additional stuff here such as additional code for timing some parts without creating branch"
    ECHO !TIME:~0,8! Now add custom additional stuff here such as additional code for timing some parts without creating branch
    PAUSE
)

ECHO !TIME:~0,8! Running locally ant clean all
CALL :RunCmdAndQuitIfFail "cd /D C:\Projects\ProjectX\hybris\bin\platform && setantenv.bat && ant clean all"
ECHO !TIME:~0,8! Running locally ant production
CALL :RunCmdAndQuitIfFail "cd /D C:\Projects\ProjectX\hybris\bin\platform && setantenv.bat && ant production"
CALL success "Deploy Status" "Everything was ok during ant clean all and ant production"

ECHO !TIME:~0,8! Creating directory /home/sshUser/newestDeploy for temporary data on server
CALL :RunPlinkAndQuitIfFail "mkdir /home/sshUser/newestDeploy"
ECHO !TIME:~0,8! Uploading hybrisServer-AllExtensions.zip
CALL :RunPscpWithCredentialsAndQuitIfFail C:\Projects\ProjectX\hybris\temp\hybris\hybrisServer\hybrisServer-AllExtensions.zip %SSH_IP%:/home/sshUser/newestDeploy/
ECHO !TIME:~0,8! Uploading hybrisServer-Platform.zip
CALL :RunPscpWithCredentialsAndQuitIfFail C:\Projects\ProjectX\hybris\temp\hybris\hybrisServer\hybrisServer-Platform.zip %SSH_IP%:/home/sshUser/newestDeploy/

ECHO !TIME:~0,8! Extracting zip files on server (about 20s)
CALL :RunPlinkAndQuitIfFail "cd /home/sshUser/newestDeploy && unzip -q hybrisServer-Platform.zip && unzip -q hybrisServer-AllExtensions.zip"

python %PROJECTS_DIR%\Scripts\py\lib\clipboard.py "@all restarting test02"
python %PROJECTS_DIR%\Scripts\py\lib\clipboard.py "@team restarting test02"
CALL info "Deploy Status" "Inform on hipchat+flowdock about server restart (test copied to clipboard)"

ECHO !TIME:~0,8! Stopping server
CALL :RunPlinkAndQuitIfFail "cd /opt/hybris/hybris6/bin/platform && ./hybrisserver.sh stop"
ECHO !TIME:~0,8! Clean old bin backup folder (~10s)
CALL :RunPlinkAndQuitIfFail "rm -rf /opt/hybris/hybris6/bin-previous"
ECHO !TIME:~0,8! Backupping current bin into bin-previous
CALL :RunPlinkAndQuitIfFail "mv /opt/hybris/hybris6/bin /opt/hybris/hybris6/bin-previous"
ECHO !TIME:~0,8! Moving bin to correct place
CALL :RunPlinkAndQuitIfFail "mv /home/sshUser/newestDeploy/hybris/bin /opt/hybris/hybris6/bin"
ECHO !TIME:~0,8! Fixing metadata: SSO related things are pointing to qa02 and should into test02
CALL :RunPlinkAndQuitIfFail "sed -i -b -e 's/qa02/test02/g' /opt/hybris/hybris6/bin/custom/project/projectstorefront/resources/metadata/hybris_sp_com.xml"
ECHO !TIME:~0,8! Cleaning temporary deploy folder
CALL :RunPlinkAndQuitIfFail "rm -fr /home/sshUser/newestDeploy"

IF %PAUSE_BEFORE_STARTING_SERVER% == 1 (
    CALL info "Deploy Status" "Now add custom additional stuff to server such as local.properties/schema changes etc before starting server"
    ECHO !TIME:~0,8! Now add custom additional stuff to server such as local.properties/schema changes etc before starting server
    PAUSE
)

REM Apply all release deploy things (for example local.properties with enabled debug logs etc.)
REM if there is anything changed in schema.xml
    REM backup old schema by moving current schema.xml to prev_schema.xml
    REM mv /opt/hybris/hybris6/config/solr/instances/default/configsets/default/conf/schema.xml /opt/hybris/hybris6/config/solr/instances/default/configsets/default/conf/prev_schema.xml

    REM copy new schema into /opt/hybris/hybris6/config/solr/instances/default/configsets/default/conf/schema.xml
    REM CALL :RunPscpWithCredentialsAndQuitIfFail C:\Projects\ProjectX\hybris\config\solr\local-customizations\schema.xml %SSH_IP%:/opt/hybris/hybris6/config/solr/instances/default/configsets/default/conf/

    REM restart solr server
    REM cd /opt/hybris/hybris6/bin/platform && . ./setantenv.sh && ant stopSolrServer startSolrServer
    REM now you can check from solr admin if everything is ok
    
ECHO !TIME:~0,8! Running remotely ant clean all
CALL :RunPlinkAndQuitIfFail "cd /opt/hybris/hybris6/bin/platform && . ./setantenv.sh && ant clean all"
ECHO !TIME:~0,8! Starting server
CALL :RunPlinkAndQuitIfFail "cd /opt/hybris/hybris6/bin/platform && ./hybrisserver.sh start"

ECHO !TIME:~0,8! Tailing output log until "Server startup in" will occur in logs
REM https://stackoverflow.com/a/6456103/4605582
REM grep -q 'PATTERN' <(tail -f file.log)
REM timeout 180 grep -q 'PATTERN' <(tail -f file.log)
REM grep -m1 'PATTERN' <(tail -f file.log) >/dev/null

REM https://unix.stackexchange.com/a/49235
REM tail -f my-file.log | tee >( grep -qx "Finished: SUCCESS" )

REM 8x% here because...function is getting 4x% to be able to run plink with effectively 2x% as parameter which is converting to one percent sign on Linux side...
REM for whitespace use \\\\s or for just space [[:space:]]. Using spaces will break this command (because of !@# bat files processor...)
REM Verbose version
CALL :RunPlinkAndQuitIfFail "sh -c 'tail --pid=$$ -f `date +"/opt/hybris/hybris6/log/tomcat/console-%%%%%%%%Y%%%%%%%%m%%%%%%%%d.log"` | { sed "/Server.startup.in/q" && kill $$; }' || echo Regex found"
REM Quiet version
REM CALL :RunPlinkAndQuitIfFail "sh -c 'tail --pid=$$ -f `date +"/opt/hybris/hybris6/log/tomcat/console-%%%%%%%%Y%%%%%%%%m%%%%%%%%d.log"` | ( grep -m1 "Server.startup.in" && kill $$; )' || echo Regex found"

IF %PAUSE_AFTER_STARTING_SERVER_BEFORE_UPDATES% == 1 (
    CALL info "Deploy Status" "Now do custom additional stuff to server such as cleaning orphaned types after starting server with new code deployed"
    ECHO !TIME:~0,8! Now do custom additional stuff to server such as cleaning orphaned types after starting server with new code deployed
    PAUSE
)

ECHO !TIME:~0,8! Updating server with "%UPDATE_SYSTEM_PARAMETERS%"

REM TODO: check also python exit status
CALL info "Deploy Status" "check also python exit status"
python %PROJECTS_DIR%\hybristools\src\update_initialize_system.py update --address=%SSH_IP% --user=%HAC_USER% --password=%HAC_PASSWORD% %UPDATE_SYSTEM_PARAMETERS%

python %PROJECTS_DIR%\Scripts\py\lib\clipboard.py "@all TEST02 updated with %UPDATE_SYSTEM_PARAMETERS:*project=project%"

ECHO !TIME:~0,8! Deploy completed successfully

ECHO !TIME:~0,8! You can check server logs by:
ECHO !TIME:~0,8! tail -f `date +"/opt/hybris/hybris6/log/tomcat/console-%%Y%%m%%d.log"`

REM -----FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS---FUNCTIONS-----

REM force execution to quit at the end of the "main" logic before going into functions section
EXIT /B %ERRORLEVEL%

:RunCmdAndQuitIfFail
ECHO Running: cmd /c %*
cmd /c %*
CALL :CommonErrorLevelHandler "CMD"
EXIT /B 0

:RunShAndQuitIfFail
ECHO Running: "C:\Program Files\Git\bin\sh.exe" -c %*
CALL "C:\Program Files\Git\bin\sh.exe" -c %*
CALL :CommonErrorLevelHandler "SH"
EXIT /B 0

:RunPlinkAndQuitIfFail
ECHO Running: plink %%SSH_IP%% -l %%SSH_USER%% -pw %%SSH_PASSWORD%% -batch %*
CALL plink %SSH_IP% -l %SSH_USER% -pw %SSH_PASSWORD% -batch %*
CALL :CommonErrorLevelHandler "Plink"
EXIT /B 0

:RunPscpWithCredentialsAndQuitIfFail
ECHO Running: pscp -l %%SSH_USER%% -pw %%SSH_PASSWORD%% -batch %*
CALL pscp -l %SSH_USER% -pw %SSH_PASSWORD% -batch %*
CALL :CommonErrorLevelHandler "Pscp"
EXIT /B 0

:CommonErrorLevelHandler
IF %ERRORLEVEL% EQU 0 (
    ECHO %~1 command executed successfully
    REM return success
    EXIT /B 0
) ELSE (
    ECHO %~1 command execution failed, exiting...
    CALL fail "Deploy Status" "Something went wrong during deploy"
    CALL ExitBatch
)