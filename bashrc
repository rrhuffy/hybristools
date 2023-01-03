# set default values if they are not set
export HYBRIS_HAC_URL=${HYBRIS_HAC_URL:-https://localhost:9002/hac}
export HYBRIS_SOLR_URL=${HYBRIS_SOLR_URL:-http://localhost:8983}
export HYBRIS_USER=${HYBRIS_USER-admin}
export HYBRIS_PASSWORD=${HYBRIS_PASSWORD-nimda}
export PROJECTS_DIR=${PROJECTS_DIR:-/mnt/c/Projects}
# TODO:
# export HYBRIS_HMC_URL=${HYBRIS_HMC_URL:-https://localhost:9002/hmc/hybris}
# export HYBRIS_BO_URL=${HYBRIS_BO_URL:-https://localhost:9002/backoffice}

# set python3 binary using global or venv version and store in PYTHON_FOR_HYBRISTOOLS
# TODO: maybe there is simpler way to use venv if exist and global python3 if someone doesn't care about venv?
PYTHON_FOR_HYBRISTOOLS=python3
if [[ -L "$PROJECTS_DIR/hybristools/venv/bin/python3" ]]; then
    PYTHON_FOR_HYBRISTOOLS="$PROJECTS_DIR/hybristools/venv/bin/python3"
fi

xs() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/execute_script.py "$@"; }
xg() { xs "$1" groovy "${@:2}"; }
xgr() { xs "$1" groovy --rollback "${@:2}"; }
# if you want to add less at end, then consider using "buffer" to avoid "Broken pipe" errors: "xyz | buffer | less -RF"
# TODO: try to find a way to preserve header while scrolling
# https://stackoverflow.com/questions/30981056/linux-shell-csv-viewer-tool-that-can-freeze-the-header
xf() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/execute_flexible_search.py "$1" "${@:2}"; }
ii() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/import_impex.py "$@"; }
sl() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/set_logger_level.py "$@"; }
sq() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/solr_query.py "$@"; }
treepywithoutcolor() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/tree.py --color none; }
ylisten() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/listen_server_logs.py "$@"; }
multiline_tabulate() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/multiline_tabulate.py "$@"; }
unroll_pk() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/unroll_pk.py "$@"; }
fill() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/fill_ignoring_ascii_escape_characters.py "$@"; }
yinit() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/update_initialize_system.py initialize "$@"; }
yinitproject() { yinit "${PROJECT_PREFIX_LONG_LOWERCASE}patches,${PROJECT_PREFIX_LONG_LOWERCASE}patches:Include test data:yes" "$@"; }
yupdate() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/update_initialize_system.py update "$@"; }
yupdateproject() { yupdate "${PROJECT_PREFIX_LONG_LOWERCASE}patches:Include test data:yes" "$@"; }
iimbo() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/hybris_import_impex_with_media_bo.py "$@"; }
iimhmc() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/hybris_import_impex_with_media_hmc.py "$@"; }

getclipboard() { xclip -selection clipboard -o; }
xgc() { xg "$(getclipboard)" "$@"; }
xgrc() { xgr "$(getclipboard)" "$@"; }
xfc() { xf "$(getclipboard)" "$@"; }
iic() { getclipboard && echo && ii "$(getclipboard)" "$@"; }

xfa() { xf "Select * from {$1}" "${@:2}"; }
xfaw() { xf "Select * from {$1} where {$2} = '$3'" "${@:4}"; }
xfawl() { xf "Select * from {$1} where {$2} like '$3'" "${@:4}"; }
xfawr() { xf "Select * from {$1} where {$2} regexp '$3'" "${@:4}"; }
xfs()  { xf "Select {$1} from {$2}" "${@:3}"; }
xfcount() { xf "Select count(*) as ${1}Count from {$1}" "${@:2}"; }
checkpatchexecutionstatus() { xf "select {patchid},{executiontime},{executionstatus} from {PatchExecution} where {rerunnable}=0 order by {executiontime} desc" $@; }
checklastpatchwitherror() { xf "select {creationtime},{name} from {PatchExecutionUnit} where {executionStatus} in ({{select {pk} from {ExecutionStatus} where {code}='ERROR'}}) order by {executiontime} desc" --width=1234|fill; }

# show all known data about Item: types inheritance, all fields with relations and 20 example items
all() { types "$1" && sid "$1" && xfa "$1" 20; }

solrgetindexes() { xf --data "select {name} from {SolrFacetSearchConfig}"; }
solrfullindex() {
    if [[ -z "$1" ]]; then
        echo "Usage: solrfullindex indexName"
        echo "To get index names use: solrgetindexes"
        return 1
    fi
    xg "indexerService.performFullIndex(facetSearchConfigService.getConfiguration('$1'))" "${@:2}";
}

solrupdate() {
    if [[ -z "$1" ]]; then
        echo "Usage: solrupdate indexName"
        echo "To get index names use: solrgetindexes"
        return 1
    fi
    xg "indexerService.updateIndex(facetSearchConfigService.getConfiguration('$1'))" "${@:2}";
}

ychecksolrindexercronjobs() { xf "select {code},{starttime},{endtime},{facetsearchconfig},{indexeroperation},{status},{result},{sessionuser} from {SolrIndexerCronJob} order by {starttime} desc" -a "$@"; }
# this is working up to about ~1905, then SAP disabled JMX in default tomcat configuration
restarthybrisserver() { xg "de.hybris.platform.jmx.JmxClient.restartWrapper(new File('../../../../data/hybristomcat.java.pid').text as Integer);"; }
xgsetonline() { xg "catalogVersionService.setSessionCatalogVersions(flexibleSearchService.search(\"select {cv.pk} from {CatalogVersion as cv join Catalog as c on {cv.catalog}={c.pk} and {cv.version}='Online'}\").result)"; }
xgsetstaged() { xg "catalogVersionService.setSessionCatalogVersions(flexibleSearchService.search(\"select {cv.pk} from {CatalogVersion as cv join Catalog as c on {cv.catalog}={c.pk} and {cv.version}='Staged'}\").result)"; }
xgsetall() { xg "catalogVersionService.setSessionCatalogVersions(flexibleSearchService.search(\"select {cv.pk} from {CatalogVersion as cv join Catalog as c on {cv.catalog}={c.pk}}\").result)"; }
runcronjob() { xg "cronJobService.performCronJob(cronJobService.getCronJob('$1'),true)" && echo "CronJob $1 started"; }
setparametertemporary() { xg "de.hybris.platform.util.Config.setParameter('$1','$2');"; }
setparametertemporarywithequals() {
    pattern='^(.+)\s*=\s*(.+)$'
    if [[ "$1" =~ $pattern ]]; then
        xg "de.hybris.platform.util.Config.setParameter('${BASH_REMATCH[1]}','${BASH_REMATCH[2]}');";
    else
        echo "Cannot find pattern: $pattern"
    fi
}
getparameter() { xg "de.hybris.platform.util.Config.getParameter('$1')" "${@:2}"; }
types() { xgr $PROJECTS_DIR/hybristools/groovy/types.groovy "${@:2}" --parameters "$1" | treepywithoutcolor; }
typesin() { xgr $PROJECTS_DIR/hybristools/groovy/typesin.groovy "${@:2}" --parameters "$1" | treepywithoutcolor; }
typesout() { xgr $PROJECTS_DIR/hybristools/groovy/types.groovy "${@:2}" --parameters "$1" | perl -pe "s/^.*?$1/$1/g" | treepywithoutcolor; }

logallwait() { sl root DEBUG && echo "Logger root changed to DEBUG" && read -p "Press Enter to continue" && echo && sl root INFO && echo "Logger root changed to INFO"; }
logallcommand() { sl root DEBUG && echo "Logger root changed to DEBUG" && $@ && echo && sl root INFO && echo "Logger root changed to INFO"; }
logallcleanlog() { egrep -v 'DefaultQueryPreprocessorRegistry|solr indexer thread|ThreadRegistry'; }

si() { xf $PROJECTS_DIR/hybristools/flexible/ShowItem 99999 "${@:2}" --parameters "$1"; }
sid() { xf $PROJECTS_DIR/hybristools/flexible/ShowItemDirect 99999 "${@:2}" --parameters "$1"; }
sidgrep() { sid "$1" | pee "head -n 1" "grep ${@:2}"; }
sidrg() { sid "$1" | pee "head -n 1" "rg ${@:2}"; }

yf() { xgr $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters "$1" | debuginfowarnerrortostderr | multiline_tabulate - -T "${@:2}"; }
yfa() { xgr $PROJECTS_DIR/hybristools/groovy/findWhoIsReferencingThisPk.groovy --parameters "$1" | unroll_pk - | debuginfowarnerrortostderr | multiline_tabulate - -T "${@:2}"; }

removeitem() {
    if [[ -z "$1" ]]; then
        echo "Usage: removeitem Type qualifier uniqueValue"
        return 1
    fi

    ii "REMOVE $1;$2[unique=true]\n;$3" "${@:4}";
}

removeitemwithduplicates() {
    if [[ -z "$1" ]]; then
        echo "Usage: removeitemwithduplicates Type qualifier uniqueOrNotValue"
        return 1
    fi

    ii "REMOVE $1[batchmode=true];itemType(code)[unique=true];$2[unique=true]\n;$1;$3";
}


removeallitems() {
    if [[ -z "$1" ]]; then
        echo "Usage: removeallitems TypeToRemoveAllItemsFrom"
        return 1
    fi

    ii "REMOVE $1[batchmode=true];itemType(code)[unique=true]\n;$1" "${@:2}";
}

updateitem() {
    if [[ -z "$1" ]]; then
        echo "Usage: updateitem typeToUpdate qualifierNameToFind qualifierValue fieldNameToSet valueToSet"
        return 1
    fi

    ii "UPDATE $1;$2[unique=true];$4\n;$3;$5" "${@:6}";
}

updateallitems() {
    if [[ -z "$1" ]]; then
        echo "Usage: updateallitems TypeToUpdateAllItems singleUniqueQualifier valueToSetForAllItems"
        return 1
    fi

    ii "UPDATE $1[batchmode=true];itemType(code)[unique=true];$2[unique=true]\n;$1;$3" "${@:4}";
}

setlocal() {
    export HYBRIS_HAC_URL="https://localhost:9002/hac"
    export HYBRIS_USER="admin"
    export HYBRIS_PASSWORD="nimda"
    export HTTP_PROXY=
    export HTTPS_PROXY=
}
setlocalwithouthacsuffix() {
    export HYBRIS_HAC_URL="https://localhost:9002"
    export HYBRIS_USER="admin"
    export HYBRIS_PASSWORD="nimda"
    export HTTP_PROXY=
    export HTTPS_PROXY=
}

logserver() { xgr "println 'tail -n ${1:-$LINES} ../../../../log/tomcat/${2:-$(date +"console-%Y%m%d.log")}'.execute().text" "${@:3}"; }
logserverwatch() { watch -c -n0 bash -i -c "'logserver $@'"; }
logserverfull() { xgr "println 'cat ../../../../log/tomcat/${2:-$(date +"console-%Y%m%d.log")}'.execute().text"; }

# versions for at least 1811 or more
accessserver() { xgr "println 'tail -n ${1:-$LINES} ../../../../log/tomcat/${2:-$(date +"access..%Y-%m-%d.log")}'.execute().text"; }
accessservergrep() { xgr "println 'grep -P $1  ../../../../log/tomcat/${2:-$(date +"access..%Y-%m-%d.log")}'.execute().text"; }
accessserverfull() { xgr "println 'cat ../../../../log/tomcat/${2:-$(date +"access..%Y-%m-%d.log")}'.execute().text"; }
# versions for 5.5, probably also 5.7 and a few 6.X versions
accessserverold() { xgr "println 'tail -n ${1:-$LINES} ../../../../log/tomcat/${2:-$(date +"access.%Y-%m-%d.log")}'.execute().text"; }
accessserveroldgrep() { xgr "println 'grep -P $1  ../../../../log/tomcat/${2:-$(date +"access.%Y-%m-%d.log")}'.execute().text"; }
accessserveroldfull() { xgr "println 'cat  ../../../../log/tomcat/${2:-$(date +"access.%Y-%m-%d.log")}'.execute().text"; }

sedcleanhybrislog() { sed -E "s/([^|]+\|){3} 20//"; }
# for VIM:          :%s/^\([^|]\+|\)\{3\} .\{11\}//
sedcleanhybrislogwithdate() { sed -E "s/([^|]+\|){3} .{11}//"; }
# for VIM:          :%s/^\([^|]\+|\)\{3\} .\{26\}//
sedcleanhybrislogwithdateandtime() { sed -E "s/([^|]+\|){3} .{26}//"; }

sedcleanspacecolumns() { sed -E "s/([^ ]+ +){$1}//"; }

# pipe DEBUG|INFO|WARN|ERROR to stderr, so it won't be picked by multiline_tabulate causing errors
# TODO: maybe just ignore DEBUG|INFO|WARN|ERROR inside multiline_tabulate, because it is used exclusively for that?
debuginfowarnerrortostderr() { pee 'grep -P "(DEBUG|INFO|WARN|ERROR):" 1>/dev/stderr' 'grep -P -v "(DEBUG|INFO|WARN|ERROR):"'; }

# TODO: simplify unroll_pk usage be either
# a) integrate unroll_pk inside execute_script (like in execute_flexible_search)
# b) leave unroll_pk separate, swallow unroll_pk arguments from ${@:4} and pass remaining ones to xg, detach it from execute_flexible_search
# Problems with version a: tightly coupled scripts, hard to debug unroll_pk when using hsi
# Problems with version b: hard to execute pipeline function and pass some arguments to first script (xg or xf) and other to unroll_pk
# TODO: create functions for filtering results to be from: Online, Staged+Online and maybe Staged version
hsi() {
    unroll_or_dummy=cat
    remaining_arguments="${@:4}"
    if [[ "$4" == "-a" ]]; then
        unroll_or_dummy="unroll_pk - $4"
        remaining_arguments="${@:5}"
    elif [[ "$4" == "-A" ]]; then
        # -A means no analyse, so don't execute unroll_pk, but swallow this argument
        remaining_arguments="${@:5}"
    else
        # TODO: check what will happen when we want (now default) analyse long but we also want to pass another argument
        unroll_or_dummy="unroll_pk -"
    fi
    # if using xgr with expect_keepass then instead of $'\36' use "'\36'" because it's adding another layer of wrapping...
    xgr $PROJECTS_DIR/hybristools/groovy/showItem.groovy --parameters "$1" "$2" "$3" $'\36' \
        | $unroll_or_dummy \
        | debuginfowarnerrortostderr \
        | sed -E '/^\{.*\}$/d' \
        | multiline_tabulate - 123456 --csv-delimiter=$'\36' ${remaining_arguments}
}

hsiwithcustomscript() {
    unroll_or_dummy=cat
    remaining_arguments="${@:5}"
    if [[ "$5" == "-a" ]]; then
        unroll_or_dummy="unroll_pk - $5"
        remaining_arguments="${@:6}"
    elif [[ "$5" == "-A" ]]; then
        # -A means no analyse, so don't execute unroll_pk, but swallow this argument
        remaining_arguments="${@:6}"
    else
        # TODO: check what will happen when we want (now default) analyse long but we also want to pass another argument
        unroll_or_dummy="unroll_pk -"
    fi
    # if using xgr with expect_keepass then instead of $'\36' use "'\36'" because it's adding another layer of wrapping...
    xgr <(echo "$1"; cat $PROJECTS_DIR/hybristools/groovy/showItem.groovy) --parameters "$2" "$3" "$4" $'\36' \
        | $unroll_or_dummy \
        | debuginfowarnerrortostderr \
        | sed -E '/^\{.*\}$/d' \
        | multiline_tabulate - 123456 --csv-delimiter=$'\36' ${remaining_arguments}
}
hsipk() { hsi Item PK "$@"; }
hsipkwithcustomscript() { hsiwithcustomscript "$1" Item PK "${@:2}"; }
clearcache() { xg 'cacheRegionProvider.getRegions().each{it.clearCache()};net.sf.ehcache.CacheManager.ALL_CACHE_MANAGERS.each{it.clearAll()};de.hybris.platform.core.Registry.getCurrentTenant().getCache().clear();null'; }
