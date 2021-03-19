hybristools
==

Collection of Hybris (SAP Commerce) tools for development, debugging and server maintenance.

I use them on a daily basis (mostly with MySQL and sometimes with SAP Cloud/Azure Database). But beware: they are not 100% bug-free, and they were not written with an idea of publishing them...so don't look at python scripts' contents, especially don't check multiline_tabulate.py until I refactor it...or if you like to analyze 400 line methods, then go ahead :D Scripts might be ugly, but they work ;)

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
   * [Find who is referencing this item](#find-who-is-referencing-this-item)
   * [Compare Staged and Online version of Item](#compare-staged-and-online-version-of-item)
   * [Get bean information](#get-bean-information)
   * [Show request mappings](#show-request-mappings)
   * [Show product's categories](#show-products-categories)
   * [Show products in category](#show-products-in-category)
   * [Synchronize catalogs](#synchronize-catalogs)
   * [Show CMSNavigationNodes](#show-cmsnavigationnodes)
   * [Flexible Search queries](#flexible-search-queries)
   * [Import impex with media](#import-impex-with-media)
   * [Update and initialize](#update-and-initialize)

<!-- Added by: rafal, at: Fri Mar 19 23:08:09 CET 2021 -->

<!--te-->
<!-- ~/gh-md-toc --no-backup $PROJECTS_DIR/hybristools/README.md -->

Installation
==

For installation instructions go to [INSTALL.md](https://github.com/rrhuffy/hybristools/blob/master/INSTALL.md)

Execute script
==
Execute script in HAC -> Console -> Scripting Languages (with selected commit or rollback mode) and return output.
Be aware that some loadbalancers have set request timeout to 60s, so you won't see results output if your script needs more than 1 minute to execute (but it will execute normally). In these situations you may need to use `Logger` to have script output in logs (example in `findWhoIsReferencingThisPk.groovy`)

Because I'm using it mostly to execute groovy scripts, I'm using bash functions to call it with groovy as a second parameter. Now I can run things with rollback mode (`xgr`) or with commit mode (`xg`) like this:

```shell
xgr 'cronJobService.getCronJob("update-backofficeIndex-CronJob").getStatus()'
xg 'cronJobService.performCronJob(cronJobService.getCronJob("update-backofficeIndex-CronJob"))'
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
If you have a flexible query saved in a file, you can insert $1, $2 inside it and use `--parameters "first" "second"` to replace them during execution. It is often used for files in folder `flexible`.

If you want continuous monitoring just add `-w 1` or `--watch 1` to execute the query with 1-second delay between executions.  

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

You can also use excel if you export a TSV (Tab separated values) file:

`xf "select {pk}, {uid}, {name}, {description}, {passwordEncoding} from {User}" 5 --pager= > output.tsv`

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
Listen to `$HYBRIS_DIR/log/tomcat/console-yyyymmdd.log` and search for server startup log (or any other regex), then you can use && to execute things like init/update, warmup storefront/backoffice, change focus to IDEA/browser, play sound, send a notification etc.
```shell
# wait until server has been started
ylisten --startup
# wait until server has been started, then start update
# (do "ant clean all && ./hybrisserver.sh debug" in a separate window before executing this command)
ylisten --startup && yupdate
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
Works in MySQL, but not in SAP Cloud, probably because of `SUBSTRING_INDEX`/`TRIM` which may be MySQL specific, also "&8192=8192" part is causing problems.

Show all fields directly accessible from given Type (`sid`)

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
Show all fields in given Type with (almost) all Items referencing it (`si`).

For example: If you are looking what uses `CMSLinkComponent` you my not find everything, because `CMSNavigationEntry` has `item` of type `Item` and it can be attached there. 
Below is example of `Media` fields, with all Items referencing it: 
<details><summary>Long output, click here to unroll</summary>

```
firstType                       | lastType                                    | qualifier           | fieldType                                | extension           | U | L | E | D | J | O | R | C
Media                           | Media                                       | altText             | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | catalog             | Catalog                                  | catalog             | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media                           | Media                                       | catalogVersion      | CatalogVersion                           | catalog             | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media                           | Media                                       | code                | java.lang.String                         | core                | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media                           | Media                                       | deniedPrincipals    | PrincipalCollection                      | core                | 0 | 0 | 1 | 1 | 0 | 1 | 0 | *
Media                           | Media                                       | derivedMedias       | Media2DerivedMediaRelderivedMediasColl   | core                | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
Media                           | Media                                       | description         | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | downloadURL         | java.lang.String                         | core                | 0 | 0 | 0 | 1 | 0 | 1 | 0 | 1
Media                           | Media                                       | folder              | MediaFolder                              | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | foreignDataOwners   | MediaCollection                          | core                | 0 | 0 | 0 | 1 | 0 | 1 | 0 | *
Media                           | Media                                       | internalURL         | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | mediaContainer      | MediaContainer                           | core                | 0 | 0 | 1 | 0 | 0 | 1 | 1 | 1
Media                           | Media                                       | mediaFormat         | MediaFormat                              | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | permittedPrincipals | PrincipalCollection                      | core                | 0 | 0 | 1 | 1 | 0 | 1 | 0 | *
Media                           | Media                                       | removable           | java.lang.Boolean                        | core                | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Media                           | Media                                       | subFolderPath       | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Media                           | Media                                       | supercategories     | CategoryMediaRelationsupercategoriesColl | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 1 | *
Media                           | Media                                       | URL                 | java.lang.String                         | core                | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1
Media                           | Media                                       | URL2                | java.lang.String                         | core                | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1
AbstractMedia                   | Media                                       | dataPK              | java.lang.Long                           | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia                   | Media                                       | location            | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia                   | Media                                       | locationHash        | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia                   | Media                                       | mime                | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia                   | Media                                       | realFileName        | java.lang.String                         | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractMedia                   | Media                                       | size                | java.lang.Long                           | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EmailMessage                    | EmailMessage                                | bodyMedia           | Media                                    | acceleratorservices | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
CompiledJasperMedia             | CompiledJasperMedia                         | compiledReport      | Media                                    | cockpit             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
RendererTemplate                | RendererTemplate                            | defaultContent      | Media                                    | commons             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
RendererTemplate                | AuditReportTemplate                         | defaultContent      | Media                                    | commons             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
SolrFacetSearchConfig           | SolrFacetSearchConfig                       | document            | Media                                    | solrfacetsearch     | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ExcelImportCronJob              | ExcelImportCronJob                          | excelFile           | Media                                    | backoffice          | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
EnumerationValue                | UserDiscountGroup                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | UserPriceGroup                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | UserTaxGroup                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | LineOfBusiness                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
...
AbstractChangeProcessorJob      | AbstractChangeProcessorJob                  | input               | Media                                    | deltadetection      | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
AbstractChangeProcessorJob      | ConsumeAllChangesJob                        | input               | Media                                    | deltadetection      | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
AbstractChangeProcessorJob      | ScriptChangeConsumptionJob                  | input               | Media                                    | deltadetection      | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
RemoveItemsCronJob              | RemoveItemsCronJob                          | itemPKs             | Media                                    | processing          | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
PointOfService                  | PointOfService                              | mapIcon             | Media                                    | basecommerce        | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
DerivedMedia                    | DerivedMedia                                | media               | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 0 | 1 | 1
CockpitUIComponentConfiguration | CockpitUIComponentConfiguration             | media               | Media                                    | cockpit             | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1
ImpExImportCronJob              | ImpExImportCronJob                          | mediasMedia         | Media                                    | impex               | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ChangeDetectionJob              | ChangeDetectionJob                          | output              | Media                                    | deltadetection      | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | Product                                     | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | VariantProduct                              | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | GenericVariantProduct                       | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | MockVariantProduct                          | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelStyleVariantProduct                  | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelSizeVariantProduct                   | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ElectronicsColorVariantProduct              | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelProduct                              | picture             | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | ConfigurationCategory                       | picture             | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | Category                                    | picture             | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | ClassificationClass                         | picture             | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | VariantCategory                             | picture             | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | VariantValueCategory                        | picture             | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
PageTemplate                    | PageTemplate                                | previewIcon         | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
PageTemplate                    | DocumentPageTemplate                        | previewIcon         | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
PageTemplate                    | EmailPageTemplate                           | previewIcon         | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | ContentPage                                 | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | AbstractPage                                | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | CategoryPage                                | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | ProductPage                                 | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | CatalogPage                                 | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | DocumentPage                                | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | EmailPage                                   | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | ProductConfigPage                           | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
AbstractPage                    | ProductConfigOverviewPage                   | previewImage        | Media                                    | cms2                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductPromotion                            | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductFixedPricePromotion                  | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
...
Principal                       | CsAgentGroup                                | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | TestEmployee                                | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | Customer                                    | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | B2BCustomer                                 | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ExcelImportCronJob              | ExcelImportCronJob                          | referencedContent   | Media                                    | backoffice          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Consignment                     | Consignment                                 | returnForm          | Media                                    | warehousing         | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ReturnRequest                   | ReturnRequest                               | returnForm          | Media                                    | basecommerce        | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Consignment                     | Consignment                                 | returnLabel         | Media                                    | warehousing         | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ReturnRequest                   | ReturnRequest                               | returnLabel         | Media                                    | basecommerce        | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Consignment                     | Consignment                                 | shippingLabel       | Media                                    | warehousing         | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Link                            | CategoryMediaRelation                       | target              | Media                                    | core                | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Link                            | HistoryDocumentRelation                     | target              | Media                                    | core                | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Link                            | ProductMediaLink                            | target              | Media                                    | core                | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1
Product                         | Product                                     | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | VariantProduct                              | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | GenericVariantProduct                       | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | MockVariantProduct                          | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelStyleVariantProduct                  | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelSizeVariantProduct                   | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ElectronicsColorVariantProduct              | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Product                         | ApparelProduct                              | thumbnail           | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | ConfigurationCategory                       | thumbnail           | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | Category                                    | thumbnail           | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | ClassificationClass                         | thumbnail           | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | VariantCategory                             | thumbnail           | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Category                        | VariantValueCategory                        | thumbnail           | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
SavedCartFileUploadProcess      | SavedCartFileUploadProcess                  | uploadedFile        | Media                                    | acceleratorservices | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
```
</details>

Find who is referencing this item
==

Do you want to know which item is referencing given item? Works with normal fields, enums, localized types, relations, CollectionTypes and...jalo/dynamic fields (but this handler is much slower that other ones).
```shell
# who uses SolrIndexConfig with name "Default" (8796093089955 in my case)?
yf 8796093089955
Type                     | pk            | qualifier                             | searchedPk
SolrFacetSearchConfig.pk | 8796093089944 | SolrFacetSearchConfig.solrIndexConfig | 8796093089955
SolrFacetSearchConfig.pk | 8796093122712 | SolrFacetSearchConfig.solrIndexConfig | 8796093089955
SolrFacetSearchConfig.pk | 8796093155480 | SolrFacetSearchConfig.solrIndexConfig | 8796093089955
SolrFacetSearchConfig.pk | 8796093188248 | SolrFacetSearchConfig.solrIndexConfig | 8796093089955

# the same but using a function with unrolling pk:
yfa 8796093089955
Type                     | pk                                            | qualifier                             | searchedPk
SolrFacetSearchConfig.pk | [SolrFacetSearchConfig](name)apparel-ukIndex  | SolrFacetSearchConfig.solrIndexConfig | [SolrIndexConfig](name)Default
SolrFacetSearchConfig.pk | [SolrFacetSearchConfig](name)apparel-deIndex  | SolrFacetSearchConfig.solrIndexConfig | [SolrIndexConfig](name)Default
SolrFacetSearchConfig.pk | [SolrFacetSearchConfig](name)powertoolsIndex  | SolrFacetSearchConfig.solrIndexConfig | [SolrIndexConfig](name)Default
SolrFacetSearchConfig.pk | [SolrFacetSearchConfig](name)electronicsIndex | SolrFacetSearchConfig.solrIndexConfig | [SolrIndexConfig](name)Default
```

Compare Staged and Online version of Item
==

```
xg $PROJECTS_DIR/hybristools/groovy/compareItemStagedAndOnline.groovy --parameters Product code 29532 $'\36' | unroll_pk - | multiline_tabulate - 12345 --csv-delimiter=$'\36' -gt --width=100
-----------------------------------------------Common-----------------------------------------------
itemtype                | ApparelProduct
code                    | 29532
ean                     | 953539556
europe1PriceFactory_PTG | eu-vat-full
europe1Prices           | [8796093219871, 8796093056031, 8796093318175]
europe1Taxes            | [8796093219870, 8796093416478, 8796093121566, 8796093350942, 8796093088798
                        | , 8796093318174, 8796093187102, 8796093383710]
galleryImages           | [[MediaContainer](qualifier)29532_1]
genders                 | [MALE]
normal                  | [[Media](code)/300Wx300H/29532_1.jpg]
numberOfReviews         | 0
others                  | [[Media](code)/1200Wx1200H/29532_1.jpg, [Media](code)/515Wx515H/29532_1.jp
                        | g, [Media](code)/300Wx300H/29532_1.jpg, [Media](code)/96Wx96H/29532_1.jpg,
                        |  [Media](code)/65Wx65H/29532_1.jpg, [Media](code)/30Wx30H/29532_1.jpg]
picture                 | [Media](code)/300Wx300H/29532_1.jpg
priceQuantity           | 1.0
reviewCount             | 0
soldIndividually        | true
supercategories         | [[Category](code)Toko, [Category](code)skigear, [Category](code)100200, [C
                        | ategory](code)snow]
thumbnail               | [Media](code)/96Wx96H/29532_1.jpg
thumbnails              | [[Media](code)/96Wx96H/29532_1.jpg]
unit                    | [Unit](code)pieces
summary[en]             | Negative side and blade angle for professional blade tuning. The tool used
                        |  by alpine World Cup pros.
name[en]                | Snowboard Ski Tool Toko Side Edge Tuning Angle Pro 87 Grad
-----------------------------------------------Unique-----------------------------------------------
-------------------------------------------------0--------------------------------------------------
1 pk                         |creationtime                |modifiedtime                |           1
2 catalogVersion              |approvalStatus|summary[de]|summary[pl]                              2
-------------------------------------------------1--------------------------------------------------
1 8796093054977              |Wed Mar 10 08:59:53 CET 2021|Fri Mar 19 21:05:23 CET 2021|           1
2 apparelProductCatalog/Staged|CHECK         |test äöü   |test żółć                                2
-------------------------------------------------2--------------------------------------------------
1 [ApparelProduct](code)29532|Wed Mar 10 09:02:25 CET 2021|Wed Mar 10 09:02:25 CET 2021|           1
2 apparelProductCatalog/Online|APPROVED      |null       |null                                     2
```

Get bean information
==

```
# print all beans from all contexts, useful when grepping through output
xg $PROJECTS_DIR/hybristools/groovy/getAllBeansFromAllContexts.groovy | grep authenticationManager
merchandisingcmswebservices/org.springframework.security.authenticationManager
occ/org.springframework.security.authenticationManager
personalizationsearchsmartedit/org.springframework.security.authenticationManager
cmssmartedit/org.springframework.security.authenticationManager
cmswebservices_junit/org.springframework.security.authenticationManager
...and more

# find bean in given context and print fields and methods
xg $PROJECTS_DIR/hybristools/groovy/getBeanFromContext.groovy --parameters backoffice backofficeLocaleService
Found backofficeLocaleService:
com.hybris.backoffice.i18n.BackofficeLocaleService@18c8b22e

Fields:
ZKSession -> null
cockpitProperties -> com.hybris.backoffice.cockpitng.util.impl.PlatformSystemPropertyResolver@309b5fcb
class -> class com.hybris.backoffice.i18n.BackofficeLocaleService
cockpitConfigurationService -> com.hybris.backoffice.config.impl.BackofficeCockpitConfigurationService@28b524f1
allUILocales -> [es_CO, pt, fr, ru, ja, zh_TW, it, ko, de, es, zh, en, hi, cs, hu, pl]
cockpitLocalesFactory -> com.hybris.cockpitng.config.locales.factory.impl.DefaultCockpitLocalesFactory@170ce4ae
allLocales -> [es_CO, in, pt, fr, ru, ja, zh_TW, it, ko, de, es, zh, en, hi, cs, hu, pl]
i18nService -> de.hybris.platform.servicelayer.i18n.impl.DefaultI18NService$$EnhancerBySpringCGLIB$$12e8f585@65d8107e
localePersistenceOnToggleEnabled -> false
currentLocale -> en_US
globalProperties -> com.hybris.backoffice.cockpitng.util.impl.PlatformSystemPropertyResolver@2815ad51

Methods:
equals
executeWithLocale
getAllLocales
getAllUILocales
getAvailableDataLocales
getClass
getCurrentLocale
getDefaultDataLocale
...and more
```

Show request mappings
==

```
xg $PROJECTS_DIR/hybristools/groovy/getRequestMappings.groovy --parameters yb2bacceleratorstorefront | multiline_tabulate - -S1
Pattern                                                      | Methods       | Controller                             | Method
[/**/c/{categoryCode:.*}/facets]                             | [GET]         | CategoryPageController                 | getFacets
[/**/c/{categoryCode:.*}/results]                            | [GET]         | CategoryPageController                 | getResults
[/**/c/{categoryCode:.*}]                                    | [GET]         | CategoryPageController                 | category
[/**/p/{productCode:.*}/configuratorPage]                    | [GET]         | ConfigureController                    | productDetail
[/**/p/{productCode:.*}/futureStock]                         | [GET]         | ProductPageController                  | productFutureStock
[/**/p/{productCode:.*}/grid/skusFutureStock]                | [POST]        | ProductPageController                  | productSkusFutureStock
[/**/p/{productCode:.*}/orderForm]                           | [GET]         | ProductPageController                  | productOrderForm
[/**/p/{productCode:.*}/quickView]                           | [GET]         | ProductPageController                  | showQuickView
[/**/p/{productCode:.*}/review]                              | [GET || POST] | ProductPageController                  | postReview
[/**/p/{productCode:.*}/reviewhtml/{numberOfReviews:.*}]     | [GET]         | ProductPageController                  | reviewHtml
[/**/p/{productCode:.*}/writeReview]                         | [GET]         | ProductPageController                  | writeReview
[/**/p/{productCode:.*}/writeReview]                         | [POST]        | ProductPageController                  | writeReview
[/**/p/{productCode:.*}/zoomImages]                          | [GET]         | ProductPageController                  | showZoomImages
[/**/p/{productCode:.*}]                                     | [GET]         | ProductPageController                  | productDetail
...and more
```

Show product's categories
==
WARNING! Replacing all "/" into "\", because "/" is used by treepywithoutcolor as a separator
```
xg $PROJECTS_DIR/hybristools/groovy/printProductCategoriesRecursively.groovy --parameters 3881061 | treepywithoutcolor
[Product](code)3881061 <Cordless drill\driver 2311> {Online}
├── [Category](code)1360 <Power Drills> {Online}
│   ├── [Category](code)1355 <Tools> {Online}
│   │   └── [Category](code)1 <Open Catalogue> {Online}
│   ├── [ClassificationClass](code)4593 <Technical details> {1.0}
│   ├── [ClassificationClass](code)4670 <Weight & dimensions> {1.0}
│   ├── [ClassificationClass](code)4671 <Energy management> {1.0}
│   └── [ClassificationClass](code)4684 <Packaging content> {1.0}
└── [Category](code)brand_4515 <Skil> {Online}
    └── [Category](code)brands <Brands> {Online}
```

Show products in category
==
WARNING! Replacing all "/" into "\", because "/" is used by treepywithoutcolor as a separator
```
xg $PROJECTS_DIR/hybristools/groovy/printProductsInsideCategory.groovy --parameters 106 | treepywithoutcolor
[106](Components)
└── [830](Cables For Computers And Peripherals)
    ├── [1505](Cable Crimpers\Cutters\Strippers)
    │   ├── 1678256 1300 Broadcast Pack
    │   └── 1678313 ProPunch™ 110
    └── [953]()
        └── 2613282 1m USA 10Gb LC\LC Duplex 50\125 Multimode Fiber Patch Cable
```

Synchronize catalogs
==

```shell
xg $PROJECTS_DIR/hybristools/groovy/synchronizeCatalog.groovy --parameters apparel Product
# then run created cronJob:
xg 'cronJobService.performCronJob(cronJobService.getCronJob("000002BG"))'
# check if it's finished
xg 'cronJobService.getCronJob("000002BG").getStatus()'
```

Show CMSNavigationNodes
==

```
xg $PROJECTS_DIR/hybristools/groovy/printCmsNavigationNodes.groovy --parameters powertoolsContentCatalog | treepywithoutcolor
root (root)
└── SiteRootNode (SiteRootNode)
    └── PowertoolsNavNode (Powertools Site)
        ├── FooterNavNode (Footer Pages)
        │   ├── FollowUsNavNode (Follow Us Pages)
        │   │   ├── AgileCommerceBlogNavNode (Agile Commerce Blog Page)
        │   │   ├── FacebookNavNode (Facebook Page)
        │   │   ├── LinkedInNavNode (LinkedIn Page)
        │   │   └── TwitterNavNode (Twitter Page)
        │   ├── SAPCommerceNavNode (SAP Commerce Cloud Pages)
        │   │   ├── AboutSAPCommerceNavNode (About SAP Commerce Cloud Page)
        │   │   └── DocumentationNavNode (Documentation Page)
        │   └── SAPCustomerExperienceNavNode (SAP Customer Experience Pages)
        │       ├── AboutSAPCustomerExperienceNavNode (About SAP Customer Experience Page)
...and more
```

Flexible Search queries
==

```
xf $PROJECTS_DIR/hybristools/flexible/CronJobsLastRunned -a
code                                       | job                                             | startTime               | duration | endTime                 | result
update-backofficeIndex-CronJob             | _solrIndexerJob                                 | 2021-03-19 21:56:06.425 | 0.0640   | 2021-03-19 21:56:06.489 | _SUCCESS
update-apparel-ukIndex-cronJob             | _solrIndexerJob                                 | 2021-03-19 21:55:46.394 | 0.3140   | 2021-03-19 21:55:46.708 | _SUCCESS
update-apparel-deIndex-cronJob             | _solrIndexerJob                                 | 2021-03-19 21:55:46.4   | 0.2940   | 2021-03-19 21:55:46.694 | _SUCCESS
update-electronicsIndex-cronJob            | _solrIndexerJob                                 | 2021-03-19 21:55:36.373 | 0.090    | 2021-03-19 21:55:36.463 | _SUCCESS
update-powertoolsIndex-cronJob             | _solrIndexerJob                                 | 2021-03-19 21:55:36.375 | 0.0860   | 2021-03-19 21:55:36.461 | _SUCCESS
000002BF                                   | _sync apparelProductCatalog:Staged-&gt;Online   | 2021-03-19 21:37:50.256 | 2.1040   | 2021-03-19 21:37:52.36  | _SUCCESS
cleanupCxPersonalizationProcessesCronJob   | _cleanupCxPersonalizationProcessJobsPerformable | 2021-03-19 21:27:33.047 | 0.020    | 2021-03-19 21:27:33.067 | _SUCCESS
xyFormHistoryRetentionCronJob              | _xyFormHistoryJob                               | 2021-03-19 21:25:42.835 | 0.020    | 2021-03-19 21:25:42.855 | _SUCCESS
cronJobHistoryRetentionCronJob             | _cronJobHistoryRetentionJob                     | 2021-03-19 21:00:09.745 | 1.3760   | 2021-03-19 21:00:11.121 | _SUCCESS
expiredInterestsCleanUpJob                 | _expiredInterestsCleanUpJob                     | 2021-03-19 21:00:09.745 | 0.0270   | 2021-03-19 21:00:09.772 | _SUCCESS
...and more

xf $PROJECTS_DIR/hybristools/flexible/ZoneDeliveryModeWithZoneAndValue
store      | zoneDeliveryMode | zdmNameEn         | zdmDescriptionEn  | zone              | value  | minimum | currency
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | china             | 27.99  | 0.0     | [Currency](isocode)EUR
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | china             | 14.49  | 0.0     | [Currency](isocode)USD
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | china             | 99.49  | 0.0     | [Currency](isocode)JPY
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | china             | 18.49  | 0.0     | [Currency](isocode)GBP
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | otherAsianRegions | 19.99  | 0.0     | [Currency](isocode)EUR
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | otherAsianRegions | 14.99  | 0.0     | [Currency](isocode)USD
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | otherAsianRegions | 99.99  | 0.0     | [Currency](isocode)JPY
apparel-de | premium-gross    | Premium Delivery  | 1-2 business days | otherAsianRegions | 10.99  | 0.0     | [Currency](isocode)GBP
...and more
```
Check also other queries in `$PROJECTS_DIR/hybristools/flexible folder`

Import impex with media
==

Opens firefox or chrome (either with GUI or headless), logs into Backoffice/HMC and imports `media.impex`
with `media.zip`. This allows for importing multiple files (like images) into Hybris.<br/>
Shortcut: <b>I</b>mport <b>I</b>mpex with <b>M</b>edia <b>BO/HMC</b>:

```shell
iimbo $PROJECTS_DIR/hybristools/impex/mediaWithZipFile.impex $PROJECTS_DIR/hybristools/impex/mediaWithZipFile.zip
iimhmc $PROJECTS_DIR/hybristools/impex/mediaWithZipFile.impex $PROJECTS_DIR/hybristools/impex/mediaWithZipFile.zip
```

Update and initialize
==

Logs into HAC -> Platform -> Update/Initialization, optionally toggle extension or change dropdown (like "sample data"
etc.) and starts the update/initialization

```shell
# update with "Include test data" set to "yes".
yupdate "projectxpatches:Include test data:yes"
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
yinit "projectxpatches:Include test data:yes"
```
