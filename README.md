hybristools
==

Collection of Hybris (SAP Commerce) tools for development, debugging and server maintenance.

<!--ts-->
   * [hybristools](#hybristools)
   * [Installation](#installation)
   * [Execute script](#execute-script)
   * [Execute flexible search](#execute-flexible-search)
      * [Multiline tabuluate](#multiline-tabuluate)
         * [CSV output](#csv-output)
   * [Import impex](#import-impex)
   * [Set logger level](#set-logger-level)
   * [Solr query](#solr-query)
   * [Listen to local server logs](#listen-to-local-server-logs)
   * [Show remote server logs](#show-remote-server-logs)
   * [Show Type inheritance tree](#show-type-inheritance-tree)
   * [Show all fields in given Type](#show-all-fields-in-given-type)
   * [TODO](#todo)
      * [Import impex with media](#import-impex-with-media)
      * [Initialize and update](#initialize-and-update)

<!-- Added by: rafal, at: Mon Mar  1 17:45:54 CET 2021 -->

<!--te-->
<!-- ~/gh-md-toc --no-backup $PROJECTS_DIR/hybristools/README.md -->

Installation
==

For installation instructions go to [INSTALL.md](https://github.com/rrhuffy/hybristools/blob/master/INSTALL.md)

Execute script
==
Execute script in HAC -> Console -> Scripting Languages (with selected commit or rollback mode) and return output.
Be aware that some loadbalancers have set request timeout to 60s, so you won't see results output if your script needs more than 1 minute to execute (but it will execute normally).

Because I'm using it mostly to execute groovy scripts, I'm using bash functions to call it with groovy as a second parameter. Now I can run things with rollback mode (`xgr`) or with commit mode (`xg`) like this:

```shell
xgr 'cronJobService.getCronJob("00000000").getStatus()'
xg my_script.groovy
```

If you have a groovy script saved in a file, you can insert $1, $2 inside it and use `--parameters "first" "second"` to replace them during execution. It is often used for files in folder `groovy/`.


Execute flexible search
==
Log into HAC, go to Console -> FlexibleSearch, execute a given query and return output.

Because I use this a lot I picked two letter shortcut for that: `xf` (e<b>X</b>ecute <b>F</b>lexible). Now to see Orders you can use:
```shell
xf "select * from {Order}"
xf "select * from {Order} where {code}=00000001"
xf "select * from {Order} where {code} like '0000000%'"
xf "select * from {Order} where {code} regexp '0000000.+'"
```
Because these queries were really frequent I also simplified them:
```shell
xfa Order
xfaw Order code 00000001
xfawl Order code '0000000%'
xfawr Order code '0000000.+'
```
If you have a flexible query saved in a file, you can insert $1, $2 inside it and use `--parameters "first" "second"` to replace them during execution. It is often used for files in folder `flexible/`.

## Multiline tabuluate

Because SQL-like queries often contains multiple columns which can't fit in terminal's window. That's why `xf` scripts uses multiline_tabulate to pretty print data:
```text
|                 terminal width 61 characters              |
# normal output when using execute_flexible_search.py with disabled pager by "--pager="
xf "select {pk}, {uid}, {name}, {description}, {passwordEncoding} from {User}" 5 --pager=
PK      uid     name    description     passwordencoding
8796093054980   admin   Administrator   administrator descrip
tion    pbkdf2
8796093087748   anonymous       Anonymous       anonymous Use
r       pbkdf2
8796093120516   searchmanager   Search Configuration ManagerS
earch Configuration Manager     pbkdf2
8796093153284   cmsreviewer     CMS Reviewer    CMS Reviewerp
bkdf2
8796093186052   cmseditor       CMS Editor      CMS Editor  p
bkdf2

# output when using execute_flexible_search.py with default pager: multiline_tabulate
xf "select {pk}, {uid}, {name}, {description}, {passwordEncoding} from {User}" 5
------------------------------0------------------------------
1 PK           |uid          |name                        | 1
2 description                 |passwordencoding             2
------------------------------1------------------------------
1 8796093054980|admin        |Administrator               | 1
2 administrator description   |pbkdf2                       2
------------------------------2------------------------------
1 8796093087748|anonymous    |Anonymous                   | 1
2 anonymous User              |pbkdf2                       2
------------------------------3------------------------------
1 8796093120516|searchmanager|Search Configuration Manager| 1
2 Search Configuration Manager|pbkdf2                       2
------------------------------4------------------------------
1 8796093153284|cmsreviewer  |CMS Reviewer                | 1
2 CMS Reviewer                |pbkdf2                       2
------------------------------5------------------------------
1 8796093186052|cmseditor    |CMS Editor                  | 1
2 CMS Editor                  |pbkdf2                       2

```
Check all options and defaults like transposing table when there is only one result by executing:
```shell
multiline_tabulate --help
```

### CSV output

Most scripts are integrated with `unroll_pk` (you can disable unrolling PK by passing
`-A` argument) and with `multiline_tabulate` (you can disable that by passing
`--pager=` argument).
This may change in future (if I find time for that) in favor of POSIX philosophy:
> Write programs that do one thing and do it well.

So instead of calling `execute_flexible_search.py "select ..."` which implicitly
uses `unroll.pk` and `multiline_tabulate` you'll need to do 
`execute_flexible_search.py "select ..." | unroll.pk - | multiline_tabulate -`, 
of course enclosed in a convenient shortcut/alias. This will allow easier debugging
specific program when weird/erroneous data is being returned.

To generate CSV output just disable pager and set csv delimiter to semicolon by `--csv-delimiter=';' --pager=`

```shell
# show first [terminal height in lines] entries with location, mime type and folder from Media type, without unrolling PK (-A)
xf "select {code}, {location}, {mime}, {folder} from {Media}" -A
# show 999999 entries but set csv delimiter to semicolon, disable pager and save output to csv file
xf "select {code}, {location}, {mime}, {folder} from {Media}" 999999 -A --csv-delimiter=';' --pager= > output.csv
```

Import impex
==

It will import impex via HAC -> Console -> ImpEx Import.
Accepting both impex in command line argument (use \n as a newline), and a path to file with impex:
```shell
# change password in B2BCustomer
ii 'UPDATE B2BCustomer; uid[unique=true]; password\n;mark.rivers@rustic-hw.com;12341234'
# import impex from file
ii $PROJECTS_DIR/projectX/task-123/huge.impex
```

Set logger level
==

It will change logger level using HAC -> Platform -> Logging

```shell
# set solrfacetsearch loggers to DEBUG
sl de.hybris.platform.solrfacetsearch DEBUG

# bash function to change root logger to DEBUG, wait for ENTER and finally set root logger back to INFO
logallwait() { sl root DEBUG && echo "Logger root changed to DEBUG" && read -p "Press Enter to continue" && echo && sl root INFO && echo "Logger root changed to INFO"; }

# bash function to change root logger to DEBUG, execute command passed as argument and finally set root logger back to INFO
logallcommand() { sl root DEBUG && echo "Logger root changed to DEBUG" && $@ && echo && sl root INFO && echo "Logger root changed to INFO"; }
```


Solr query
==

Execute a query on given index. Checks whether flip or flop is newer (if exists).

```shell
# example query if there is only one index (excluding backoffice one)
sq '*:*'
# example query if there are more than one index (excluding backoffice one)
sq '*:*' --index=powertoolsIndex
# example queries with data filtering using jq: https://stedolan.github.io/jq/manual/
# show only documents, without SOLR metadata
sq '*:*' | jq '.response.docs[]'
# show only first document
sq '*:*' | jq '.response.docs[0]'
# show first two documents
sq '*:*' | jq '.response.docs[:2]'
# show only pk, code and catalogVersion from all results
sq '*:*' | jq '.response.docs[] | {pk, code_string, catalogVersion}'
# another way to show only pk, code and catalogVersion is to use "gron":
sq '*:*' | gron | grep -P 'pk|code_string|catalogVersion'
# if you want to rerun a real query then enable SOLR logger by command below and reuse query from logs
sl de.hybris.platform.solrfacetsearch.search.impl.DefaultFacetSearchStrategy DEBUG 
```

Listen to local server logs
==
Listen to `$HYBRIS_DIR/log/tomcat/console-yyyymmdd.log` and search for server startup log (or any other regex), then you can use pipe to execute things like init/update, warmup storefront/backoffice, change focus to IDEA/browser, play sound, send a notification etc.
```shell
# wait until server has been started
ylisten --startup
# wait until server has been started, then start update
# (do "ant clean all && ./hybrisserver.sh debug" in a separate window before executing this command)
ylisten --startup | yupdate
```

Show remote server logs
==
Run a groovy to retrieve a console or access logs using path traversal exploit.

It works only on servers with default log path, because ot that it doesn't work on SAP Cloud!  
```shell
# show last [terminal height in lines] console log lines 
logserver
...
INFO   | jvm 1    | main    | 2021/02/27 11:32:14.797 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Started indexer cronjob.
INFO   | jvm 1    | main    | 2021/02/27 11:32:14.797 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Finished indexer cronjob.
# show last 3 lines of console logs
logserver 3
INFO   | jvm 1    | main    | 2021/02/27 11:35:14.900 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Started indexer cronjob.
INFO   | jvm 1    | main    | 2021/02/27 11:35:15.000 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Finished indexer cronjob.
INFO   | jvm 1    | main    | 2021/02/27 11:35:15.516 |
# show console logs but remove first 3 columns and first 2 digits from fourth (leaving shortened date visible):
logserver | sedcleanhybrislog
21/02/27 11:36:14.939 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Started indexer cronjob.
21/02/27 11:36:14.939 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Finished indexer cronjob.
21/02/27 11:36:15.452 |
# show console logs but remove first 4 columns (filter out date part):
logserver | sedcleanhybrislogwithdate
11:36:14.939 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Started indexer cronjob.
11:36:14.939 | INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Finished indexer cronjob.
11:36:15.452 |
# show console logs but remove first 4 columns (filter out date and time):
logserver | sedcleanhybrislogwithdateandtime
INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Started indexer cronjob.
INFO  [update-backofficeIndex-CronJob::de.hybris.platform.servicelayer.internal.jalo.ServicelayerJob] (update-backofficeIndex-CronJob) [SolrIndexerJob] Finished indexer cronjob.

# constantly update last 10 lines (with 0.1s wait time in watch + about 0.5s/2s for retrieve logs locally/remotely)
logserverwatch '10 | sedcleanhybrislogwithdate'

# show today's access logs from server (normal version for at least 1811 or more, old version for 5.5, probably also 5.7 and a few 6.X versions)
accessserver
accessserverold

# grep in access logs (example for searching POST requests with 200 status and 3+ digit response size)
accessservergrep 'POST.+200\\s\\d{3,}'
accessserveroldgrep 'POST.+200\\s\\d{3,}'

# get full access file for further local processing
accessserverfull > full.access.log
accessserveroldfull > full.access.log
```

Show Type inheritance tree
==

`typesin Product`
```text
Item
└── ExtensibleItem
    └── LocalizableItem
        └── GenericItem
            └── Product
```

`typesout Product`
```text
Product
├── ApparelProduct
└── VariantProduct
    ├── ApparelStyleVariantProduct
    │   └── ApparelSizeVariantProduct
    ├── ElectronicsColorVariantProduct
    ├── GenericVariantProduct
    └── MockVariantProduct
```

`types Product`
```text
Item
└── ExtensibleItem
    └── LocalizableItem
        └── GenericItem
            └── Product
                ├── ApparelProduct
                └── VariantProduct
                    ├── ApparelStyleVariantProduct
                    │   └── ApparelSizeVariantProduct
                    ├── ElectronicsColorVariantProduct
                    ├── GenericVariantProduct
                    └── MockVariantProduct
```

Show all fields in given Type
==
Show all fields in given Type directly without incoming relations (`sid`)<br/>
Also show all Types with incoming relations to given Type (`si`)
```text
# show all fields accessible directly from Product type, sorted by unique fields (fifth column)
# modifiers explanation: Unique, Localized, Editable, Dynamic, Jalo, Optional, Relation, Cardinality
xf flexible/ShowItemDirect -p Media -s5
# using "sid" (ShowItemDirect) shortcut
sid Media -s5
firstType     | qualifier           | fieldType                                | extension | U | L | E | D | J | O | R | C
Media         | catalogVersion      | CatalogVersion                           | catalog   | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media         | code                | java.lang.String                         | core      | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media         | altText             | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | catalog             | Catalog                                  | catalog   | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media         | deniedPrincipals    | PrincipalCollection                      | core      | 0 | 0 | 1 | 1 | 0 | 1 | 0 | *
Media         | derivedMedias       | Media2DerivedMediaRelderivedMediasColl   | core      | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
Media         | description         | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | downloadURL         | java.lang.String                         | core      | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1
Media         | folder              | MediaFolder                              | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | foreignDataOwners   | MediaCollection                          | core      | 0 | 0 | 0 | 1 | 0 | 1 | 0 | *
Media         | internalURL         | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | mediaContainer      | MediaContainer                           | core      | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1
Media         | mediaFormat         | MediaFormat                              | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | permittedPrincipals | PrincipalCollection                      | core      | 0 | 0 | 1 | 1 | 0 | 1 | 0 | *
Media         | removable           | java.lang.Boolean                        | core      | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media         | subFolderPath       | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media         | supercategories     | CategoryMediaRelationsupercategoriesColl | catalog   | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
Media         | URL                 | java.lang.String                         | core      | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1
Media         | URL2                | java.lang.String                         | core      | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1
AbstractMedia | dataPK              | java.lang.Long                           | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia | location            | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia | locationHash        | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia | mime                | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia | realFileName        | java.lang.String                         | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia | size                | java.lang.Long                           | core      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
```

TODO
==
- remaining files from Scripts/py
- flexible/ - folder with frequent flexible search queries
- groovy/ - folder with frequent groovy scripts
- selenium scripts (already written, need only selenium installation instructions)

<details><summary>TODO: Selenium scripts, needs selenium installation instructions</summary>

## Import impex with media
Opens firefox or chrome (either with GUI or headless), logs into Backoffice/HMC
and imports `media.impex` with `media.zip`. This allows for importing multiple
files (like images) into Hybris.<br/>
Shortcut: <b>I</b>mport <b>I</b>mpex with <b>M</b>edia <b>BO/HMC</b>:
```shell
iimbo path/to/media.impex path/to/media.zip
iimhmc path/to/media.impex path/to/media.zip
# TODO: test
```

## Initialize and update
Logs into HAC -> Platform -> Initialization/Update, optionally toggle extension or change dropdown (like "sample data" etc.) and starts the initialization/update
```shell
# prepare for system initialization, but wait for enter before clicking "Initialize" button
# so you can see if everything is selected properly.
# Useful when you have to test if you correctly set changes in extensions.
yinit --pause
# prepare for system initialization, but sleep for 10 seconds before clicking "Initialize" button, can be aborted by CTRL+C
# so you can see if everything is selected properly.
# Useful when you have to test if you correctly set changes in extensions.
yinit --sleep
# prepare for system initialization and start immediately
yinit
# initialize with "Include test data" set to "yes".
# "projectxpatches" is twice, because when initializing "projectxpatches" is selected, so first deselect that, and then select with additional changes.
yinit "projectxpatches,projectxpatches:Include test data:yes"
# update with "Include test data" set to "yes".
# "projectxpatches" is once, because when updating "projectxpatches" is not selected, so select with additional changes.
yupdate "projectxpatches:Include test data:yes"
# TODO: test
```

</details>
