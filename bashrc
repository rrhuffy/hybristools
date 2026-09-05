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
export PYTHON_FOR_HYBRISTOOLS=python3
if [[ -L "$PROJECTS_DIR/hybristools/venv/bin/python3" ]]; then
    export PYTHON_FOR_HYBRISTOOLS="$PROJECTS_DIR/hybristools/venv/bin/python3"
fi

xs() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/execute_script.py "$@"; }
xg() { xs "$1" groovy "${@:2}"; }
xgr() { xs "$1" groovy --rollback "${@:2}"; }
# if you want to add less at end, then consider using "buffer" to avoid "Broken pipe" errors: "xyz | buffer | less -RF"
# TODO: try to find a way to preserve header while scrolling (use ov instead of less as pager?)
# https://stackoverflow.com/questions/30981056/linux-shell-csv-viewer-tool-that-can-freeze-the-header
xf() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/execute_flexible_search.py "$1" "${@:2}"; }
ii() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/import_impex.py "$@"; }
sl() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/set_logger_level.py "$@"; }
sld() { sl "$@" DEBUG; }
sli() { sl "$@" INFO; }
sldw() { sl "$@" DEBUG && read -p "$@ set to DEBUG, press Enter to change it back to INFO" && echo && sl "$@" INFO; echo "Reverted $@ back to INFO"; }
sq() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/solr_query.py "$@"; }
treepywithoutcolor() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/tree.py --color none; }
ylisten() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/listen_server_logs.py "$@"; }
multiline_tabulate() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/multiline_tabulate.py "$@"; }
alias mt=multiline_tabulate
unroll_pk() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/unroll_pk.py "$@"; }
unroll_pk_groovy() { base64 -w0 | xg "$PROJECTS_DIR/hybristools/groovy/unrollPk.groovy" --parameters "$@"; }
fill() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/fill_ignoring_ascii_escape_characters.py "$@"; }
yinit() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/update_initialize_system.py initialize "$@"; }
yinitproject() { yinit "${PROJECT_PREFIX_LONG_LOWERCASE}patches,${PROJECT_PREFIX_LONG_LOWERCASE}patches:Include test data:yes" "$@"; }
yupdate() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/update_initialize_system.py update "$@"; }
yupdateproject() { yupdate "${PROJECT_PREFIX_LONG_LOWERCASE}patches" "$@"; }
iimbo() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/hybris_import_impex_with_media_bo.py "$@"; }
iimhmc() { $PYTHON_FOR_HYBRISTOOLS $PROJECTS_DIR/hybristools/src/hybris_import_impex_with_media_hmc.py "$@"; }

getclipboard() { xclip -selection clipboard -o; }
realignclipboard() { getclipboard | multiline_tabulate --csv-delimiter=\| | setclipboard ; }
xgc() { getclipboard > /dev/stderr; xg "$(getclipboard)" "$@"; }
xgrc() { getclipboard > /dev/stderr; xgr "$(getclipboard)" "$@"; }
xfc() { getclipboard > /dev/stderr; xf "$(getclipboard)" "$@"; }
iic() { getclipboard > /dev/stderr; ii "$(getclipboard)" "$@"; }

xfa() { xf "Select * from {$1}" "${@:2}"; }
xfaw() { xf "Select * from {$1} where {$2} = '$3'" "${@:4}"; }
xfawl() { xf "Select * from {$1} where {$2} like '$3'" "${@:4}"; }
xfawr() { xf "Select * from {$1} where {$2} regexp '$3'" "${@:4}"; }
xfs()  { xf "Select {$1} from {$2}" "${@:3}"; }
xfcount() { xf "Select count(*) as ${1}Count from {$1}" "${@:2}"; }

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
runcronjob() { xg "cronJobService.performCronJob(cronJobService.getCronJob('$1'),true)" "${@:2}" && echo "CronJob $1 started and ended"; }
runcronjobasync() { xg "cronJobService.performCronJob(cronJobService.getCronJob('$1'),false)" "${@:2}" && echo "CronJob $1 started asynchronously"; }
setparametertemporary() { xg "de.hybris.platform.util.Config.setParameter('$1','$2'); org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info(\"Setting $1 to $2 until node restart\")"; }
setparametertemporarywithequals() {
    pattern='^(.+)\s*=\s*(.+)$'
    if [[ "$1" =~ $pattern ]]; then
        xg "de.hybris.platform.util.Config.setParameter('${BASH_REMATCH[1]}','${BASH_REMATCH[2]}'); org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info(\"Setting ${BASH_REMATCH[1]} to ${BASH_REMATCH[2]} until node restart\")";
    else
        echo "Cannot find pattern: $pattern"
    fi
}
getparameter() { xg "de.hybris.platform.util.Config.getParameter('$1')" "${@:2}"; }
getparameters() { xg "de.hybris.platform.util.Config.getParametersByPattern('$1').each{println \"\$it.key=\$it.value\"}" "${@:2}"; }
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
    if [[ -z "$3" ]]; then
        echo "Usage: removeitem Type qualifier uniqueValue"
        return 1
    fi

    echo "REMOVE $1;$2[unique=true]\n;$3" "${@:4}";
    ii "REMOVE $1;$2[unique=true]\n;$3" "${@:4}";
}
removeItemPk() { removeitem Item PK "$1"; }

removeitemwithduplicates() {
    if [[ -z "$3" ]]; then
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
    if [[ -z "$5" ]]; then
        echo "Usage: updateitem typeToUpdate qualifierNameToFind qualifierValue fieldNameToSet valueToSet"
        return 1
    fi

    echo -e "UPDATE $1;$2[unique=true];$4\n;$3;$5" "${@:6}";
    ii "UPDATE $1;$2[unique=true];$4\n;$3;$5" "${@:6}";
}
# when we provide last parameters: "code" "x" it will call .setCode(x)
# tested value examples:
# ''
# false
# 'java.util.Date.from(java.time.LocalDate.now().atStartOfDay(java.time.ZoneId.systemDefault()).toInstant())'
# 'new java.text.SimpleDateFormat("yyyyMMddHHmmss").parse("20250923134500")'
updateitemgroovy() {
    if [[ -z "$5" ]]; then
        echo "Usage: updateitemgroovy typeToUpdate qualifierNameToFind qualifierValue fieldNameToSet(PascalCase or camelCase) valueToSet('', false, 'new Date()')"
        return 1
    fi

    xg - <<-EOF
    query = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("select {pk} from {$1} where {$2}='$3'")
    result = flexibleSearchService.searchUnique(query)
    result.set${4^}($5)
    modelService.save(result)
EOF
}

changepassword() {
    if [[ -z "$2" ]]; then
        echo "Usage: changepassword qualifierLikeEmailOrUid valueOfEmailOrUid [newPasswordOrWillBe:testtest]"
        return 1
    fi

    xg - <<-EOF
    query = new de.hybris.platform.servicelayer.search.FlexibleSearchQuery("select {pk} from {B2BCustomer} where {$1}='$2'")
    result = flexibleSearchService.searchUnique(query)
    result.setLoginDisabled(false)
    result.setEncodedPassword("${3:-testtest}")
    result.setPasswordEncoding("*")
    modelService.save(result)
EOF
}

updateallitems() {
    if [[ -z "$3" ]]; then
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
# https://superuser.com/questions/380772/removing-ansi-color-codes-from-text-stream/380778#380778
# \x1b\[[0-9;]*m
# https://stackoverflow.com/questions/17998978/removing-colors-from-output
sedcleanansicolors() { sed -r "s/\x1B\[([0-9]{1,3}(;[0-9]{1,2};?)?)?[mGK]//g"; }
sedcleanhybrislogwithdateandtimeandlevelandthread() { sedcleanhybrislogwithdateandtime | sedcleanansicolors | sed -E 's/[A-Z]+\s+\[[^]]+\]\s*//'; }


sedcleanspacecolumns() { sed -E "s/([^ ]+ +){$1}//"; }

# pipe DEBUG|INFO|WARN|ERROR to stderr, so it won't be picked by multiline_tabulate causing errors
# TODO: maybe just ignore DEBUG|INFO|WARN|ERROR inside multiline_tabulate, because it is used exclusively for that?
debuginfowarnerrortostderr() { pee 'grep -P "(DEBUG|INFO|WARN|ERROR):" 1>/dev/stderr' 'grep -P -v "(DEBUG|INFO|WARN|ERROR):"'; }

# pipeline_router: Universal pipeline builder and argument router.
# As alternative to python architecture like in show_item.py which calls HAC, then imports unroll + multiline_tabulate
# which gives single source of truth and rich argument parsing via argparse (subcommands, typed flags, built-in --help)
# but won't solve generic shell pipeline problem: non python tools (hsort) + in-memory bash functions, and 0ms stream piping
#
# Syntax:
#   pipeline_router "cmd1" "cmd2" ... ::: [args...]
#
# Routing Rules:
#   1. Default Target: Plain arguments before any '--' go to the first command (Stage 1).
#   2. Sequential '--': Advances argument collection to the next command from left to right.
#   3. Targeted 'N:flag' or 'L:flag': Direct injection to Stage N (1-indexed) or L (last command).
#      - Single flag / attached:  L:--csv, 3:--csv, 2:-A, 2:-a, 3:--csv-delimiter=,
#      - Space-delimited value:   2:"-k 2" (or use sequential '-- -k 2')
#   4. Sub-pipe Chaining: Commands defined with pipes (e.g. "grep ... | sort -n") run intermediate
#      filters untouched; routed arguments attach directly to the final command in that sub-chain.
#      For static postfix sinks (e.g. '| less -RF'), pipe outside: pipeline_router ... ::: "$@" | less -RF
#
# Dry-run Inspection:
#   Set DRY_RUN=1 or N=1 to print the assembled pipeline to stderr without executing:
#     DRY_RUN=1 hsi Product code FOO -A L:--csv
#     N=1 hsi Product code FOO 2:-a 3:--csv
#
# Linearized Examples:
#   cat names.txt | pipeline_router "grep" "sort" "uniq" "head" ::: "john" -- -f -- -c -- -n 5
#   hsi Product code FOO                                  # Plain args -> Stage 1 (query)
#   hsi Product code FOO -- -A                            # Advance to Stage 2 (unroll_pk) via '--'
#   hsi Product code FOO 2:-A                             # Targeted Stage 2 via 2: (no '--' needed)
#   hsi Product code FOO L:--csv                          # Targeted last stage via L: (multiline_tabulate)
#   hsi Product code FOO 2:-A L:--csv                     # Targeted Stage 2 (-A) and last stage (--csv)
#   hsi Product code FOO -- -A -- --csv                   # Equivalent using sequential '--' boundaries
#   N=1 hsi Product code FOO -A L:--csv                   # Dry-run: print pipeline without executing
pipeline_router() {
    [ $# -eq 0 ] && return 0
    local cmds=()
    while [ $# -gt 0 ] && [ "$1" != ":::" ]; do
        cmds+=("$1")
        shift
    done

    [ "$1" != ":::" ] && { echo "pipeline_router: missing ':::' separator between commands and arguments" >&2; return 1; }
    shift

    local num_cmds=${#cmds[@]}
    [ $num_cmds -eq 0 ] && { echo "pipeline_router: no commands specified before ':::'" >&2; return 1; }

    local stage=0
    local -a stage_args
    for ((i=0; i<num_cmds; i++)); do stage_args[i]=""; done

    for arg in "$@"; do
        if [ "$arg" = "--" ]; then
            ((stage++))
            if [ $stage -ge $num_cmds ]; then
                echo "pipeline_router: too many '--' stage separators (max $((num_cmds - 1)))" >&2
                return 1
            fi
        # Targeted shortcut: N:flag (1-indexed, e.g. 3:--csv) or L:flag (last command)
        elif [[ "$arg" =~ ^([1-9][0-9]*|[Ll]):(.*)$ ]]; then
            local stage_tok="${BASH_REMATCH[1]}"
            local target_flag="${BASH_REMATCH[2]}"
            # Map numeric 1..N or L/l directly to stage index (0-indexed)
            local target_idx
            [[ "$stage_tok" == [Ll] ]] && target_idx=$((num_cmds - 1)) || target_idx=$((stage_tok - 1))
            if [ $target_idx -lt $num_cmds ]; then
                stage_args[$target_idx]+=" $(printf '%q' "$target_flag")"
            else
                echo "pipeline_router: stage $arg out of range (1-$num_cmds)" >&2
                return 1
            fi
        else
            if [ $stage -lt $num_cmds ]; then
                stage_args[$stage]+=" $(printf '%q' "$arg")"
            fi
        fi
    done

    # Dynamically build pipeline
    local pipeline=""
    for i in "${!cmds[@]}"; do
        [ $i -gt 0 ] && pipeline+=" | "
        pipeline+="${cmds[$i]}${stage_args[$i]}"
    done

    # Single-line dry-run feature (DRY_RUN=1 or N=1)
    [ -n "$DRY_RUN" ] || [ "${N:-}" = "1" ] && { echo "DRY_RUN: $pipeline" >&2; return 0; }

    eval "$pipeline"
}

# Examples:
#   hsi Product code FOO                 # Default: show item, unroll PKs, tabulate output
#   hsi Product code FOO -A              # Muscle memory: -A skips unroll_pk (Stage 2)
#   hsi Product code FOO -a              # Muscle memory: -a runs unroll_pk with -a (Stage 2)
#   hsi Product code FOO --csv           # Muscle memory: bare flags -> multiline_tabulate (Last stage)
#   hsi Product code FOO -g -T           # Short flags (-g: group, -T: no-transpose) -> multiline_tabulate (Last stage)
#   hsi Product code FOO -A --csv        # -A to unroll_pk, --csv to multiline_tabulate
#   hsi Product code FOO 2:-A L:--csv    # Explicit routing: 2: (unroll_pk), L: (multiline_tabulate)
#   N=1 hsi Product code FOO -A L:--csv  # Dry-run: print pipeline without executing (or DRY_RUN=1)
hsi() {
    local t=$1 q=$2 v=$3
    shift 3 2>/dev/null || { echo "Usage: hsi <ItemType> <QualifierField> <QualifierValue> [flags...]" >&2; return 1; }
    local qt=$(printf '%q' "$t")
    local qq=$(printf '%q' "$q")
    local qv=$(printf '%q' "$v")

    # Preserve muscle memory: translate -a/-A -> 2:, and all other flags/values -> 3:
    local -a routed=()
    for arg in "$@"; do
        case "$arg" in
            -a|-A)           routed+=("2:$arg") ;; # Muscle memory: unroll_pk (Stage 2)
            [1-9]*:*|[Ll]:*) routed+=("$arg")   ;; # Explicit routing (1:, 2:, 3:, L:) passes as-is
            --)              routed+=("$arg")   ;; # Explicit stage separator passes as-is
            -*)              routed+=("3:$arg") ;; # Any other flag (-g, -T, --csv) -> Stage 3 (multiline_tabulate)
            *)               routed+=("3:$arg") ;; # Trailing values (e.g. limit) -> Stage 3 (multiline_tabulate)
        esac
    done

    # if using xgr with expect_keepass then instead of $'\36' use "'\36'" because it's adding another layer of wrapping...
    pipeline_router \
        "xgr $PROJECTS_DIR/hybristools/groovy/showItem.groovy --parameters $qt $qq $qv \$'\\36'" \
        "unroll_pk -" \
        "debuginfowarnerrortostderr | sed -E '/^\\{.*\\}\$/d' | multiline_tabulate - 123456 --csv-delimiter=\$'\\36'" \
        ::: "${routed[@]}"
}

# Examples:
#   hsiwithcustomscript "script_code" Product code FOO -A
#   hsiwithcustomscript "script_code" Product code FOO --csv
hsiwithcustomscript() {
    local script=$1 t=$2 q=$3 v=$4
    shift 4 2>/dev/null || { echo "Usage: hsiwithcustomscript <custom_groovy_script> <ItemType> <QualifierField> <QualifierValue> [flags...]" >&2; return 1; }
    local qscript=$(printf '%q' "$script")
    local qt=$(printf '%q' "$t")
    local qq=$(printf '%q' "$q")
    local qv=$(printf '%q' "$v")

    # Preserve muscle memory: translate -a/-A -> 2:, and all other flags/values -> 3:
    local -a routed=()
    for arg in "$@"; do
        case "$arg" in
            -a|-A)           routed+=("2:$arg") ;; # Muscle memory: unroll_pk (Stage 2)
            [1-9]*:*|[Ll]:*) routed+=("$arg")   ;; # Explicit routing (1:, 2:, 3:, L:) passes as-is
            --)              routed+=("$arg")   ;; # Explicit stage separator passes as-is
            -*)              routed+=("3:$arg") ;; # Any other flag (-g, -T, --csv) -> Stage 3 (multiline_tabulate)
            *)               routed+=("3:$arg") ;; # Trailing values (e.g. limit) -> Stage 3 (multiline_tabulate)
        esac
    done

    # if using xgr with expect_keepass then instead of $'\36' use "'\36'" because it's adding another layer of wrapping...
    pipeline_router \
        "xgr <(printf '%s\n' $qscript; cat \$PROJECTS_DIR/hybristools/groovy/showItem.groovy) --parameters $qt $qq $qv \$'\\36'" \
        "unroll_pk -" \
        "debuginfowarnerrortostderr | sed -E '/^\\{.*\\}\$/d' | multiline_tabulate - 123456 --csv-delimiter=\$'\\36'" \
        ::: "${routed[@]}"
}
hsipk() { hsi Item PK "$@"; }
hsipkwithcustomscript() { hsiwithcustomscript "$1" Item PK "${@:2}"; }
# history | awk '{print $4, $5, $6}' | sort | uniq -c | sort -n | tail
# this showed that...`hsi Product code` is most used `hsi` command
hsipc() { hsi Product code "$@"; }
clearcache() { xg 'cacheRegionProvider.getRegions().each{it.clearCache()};net.sf.ehcache.CacheManager.ALL_CACHE_MANAGERS.each{it.clearAll()};de.hybris.platform.core.Registry.getCurrentTenant().getCache().clear();org.apache.log4j.Logger.getLogger(de.hybris.platform.servicelayer.internal.jalo.ScriptingJob).info("Cleared caches");"Cleared caches"'; }
cc() { clearcache; }
waitForHybris() {
    # longer/better version of
    # until curl -o /dev/null -s -m1 -k -f $HYBRIS_HAC_URL; do echo "waiting for hybris..."; sleep 0.1; done;
    echo -n "waiting for hybris..."
    counter=0
    until curl -o /dev/null -s -m1 -k -f $HYBRIS_HAC_URL; do
#        [ $(( $counter % 5 )) -eq 0 ] && echo -n "."
        echo -n "."
        counter=$((counter + 1))
        sleep 0.1
    done
    echo "done"
}

# TODO: name instead of pretty print (of base/variant product codes)
pp() { xgr $PROJECTS_DIR/hybristools/groovy/printBaseProductAndVariants.groovy --parameters "$1" "${2:-$COLUMNS}"; }
