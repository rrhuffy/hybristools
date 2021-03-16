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
Be aware that some loadbalancers have set request timeout to 60s, so you won't see results output if your script needs more than 1 minute to execute (but it will execute normally). In these situations you may need to use `System.out.println`/`Logger` to have script output in logs

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
Works in MySQL, because of `SUBSTRING_INDEX`. SAP Cloud is in TODO probably because of used `SUBSTRING_INDEX` or `TRIM` which may be MySQL specific

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
EnumerationValue                | RetentionState                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CustomerType                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | Gender                                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PhoneContactInfoType                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DeliveryStatus                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PaymentStatus                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderStatus                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ExportStatus                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CheckoutPaymentType                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ImportStatus                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SalesApplication                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ReturnFulfillmentStatus                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | QuoteState                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CreditCardType                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductPriceGroup                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductTaxGroup                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductDiscountGroup                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderEntryStatus                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PickupInStoreMode                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EncodingEnum                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BarcodeType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
JasperMedia                     | JasperMedia                                 | icon                | Media                                    | cockpit             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
JasperMedia                     | CompiledJasperMedia                         | icon                | Media                                    | cockpit             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ArticleApprovalStatus                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SavedValueEntryType                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ScriptType                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | documentTypeEnum                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RendererTypeEnum                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ErrorMode                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | JobLogLevel                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CronJobStatus                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CronJobResult                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BooleanOperator                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ImpExValidationModeEnum                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ExportConverterEnum                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IndexerOperationValues                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductConfigurationPersistenceCleanUpMode  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DistributedProcessState                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ActionType                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProcessState                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | WarehouseConsignmentState                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | NotificationType                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BatchType                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | Severity                                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ValidatorLanguage                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ConfiguratorType                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductInfoStatus                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductReference                | ProductReference                            | icon                | Media                                    | catalog             | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductReferenceTypeEnum                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductDifferenceMode                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CategoryDifferenceMode                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ClassificationAttributeTypeEnum             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ClassificationAttributeVisibilityEnum       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AdvancedQueryComparatorEnum                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EmptyParamEnum                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EnumerationValue                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PriceRowChannel                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | WorkflowActionType                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | WorkflowActionStatus                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsInterventionType                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsEventReason                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsResolutionType                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsFacetsMergeMode                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsBoostItemsMergeMode                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsBoostRulesMergeMode                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsSortsMergeMode                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsFacetType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsBoostOperator                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsBoostType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsSortOrder                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DestinationChannel                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RegistrationStatus                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EventPriority                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EventMappingType                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IntervalResolution                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FraudStatus                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ConsignmentStatus                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | InStockStatus                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | StockLevelUpdateType                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DistanceUnit                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | WeekDay                                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PointOfServiceTypeEnum                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderModificationEntryStatus                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderCancelEntryStatus                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CancelReason                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ReturnStatus                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ReturnAction                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ReplacementReason                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RefundReason                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SiteTheme                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SiteChannel                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ABTestScopes                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | LinkTargets                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CmsSiteContext                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FlashQuality                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FlashScale                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FlashWmode                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FlashSalign                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CarouselScroll                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RotatingImagesComponentEffect               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductListLayouts                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CartTotalDisplayType                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | NavigationBarMenuLayout                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ScrollType                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | YFormDataActionEnum                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CmsApprovalStatus                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CmsItemDisplayStatus                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CmsPageStatus                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CmsRobotTag                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | UiExperienceLevel                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | LiveEditVariant                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CockpitSpecialCollectionType                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CustomerReviewApprovalType                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ItemVersionMarkerStatus                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IntegrationType                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ItemTypeMatchEnum                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IntegrationRequestStatus                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | HttpMethod                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AuthenticationType                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PaymentTransactionType                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RuleType                                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProductConfigRuleMessageSeverity            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DroolsEqualityBehavior                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DroolsEventProcessingMode                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DroolsSessionType                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RuleStatus                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | KeywordRedirectMatchType                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrPropertiesTypes                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrIndexedPropertyFacetType                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrWildcardType                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrIndexedPropertyFacetSort                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IndexMode                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrCommitMode                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrOptimizeMode                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrServerModes                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrQueryMethod                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IndexerOperationStatus                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SolrItemModificationType                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
StoreLocatorFeature             | StoreLocatorFeature                         | icon                | Media                                    | commerceservices    | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | B2BBookingLineStatus                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BookingType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | B2BPeriodRange                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | B2BRateType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | MerchantCheckStatus                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | MerchantCheckStatusEmail                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PermissionStatus                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BundleRuleTypeEnum                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | BundleTemplateStatusEnum                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EntitlementTimeUnit                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SiteMessageType                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CxItemStatus                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CxGroupingOperator                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CxCatalogLookupType                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CxUserType                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsEmailRecipients                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsTicketCategory                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsTicketPriority                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CsTicketState                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ExportDataStatus                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SiteMapPageEnum                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SiteMapChangeFrequencyEnum                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DocumentStatus                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DocumentPayableOrUsable                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ConversationStatus                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | couponNotificationStatus                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DeclineReason                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | AsnStatus                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | Wishlist2EntryPriority                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | YFormDefinitionStatusEnum                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | YFormDataTypeEnum                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RelationEndCardinalityEnum                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | TypeOfCollectionEnum                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | TestEnum                                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | MediaManagementTypeEnum                     | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | GroupType                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DayOfWeek                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ImpExProcessModeEnum                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ScriptModifierEnum                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ScriptTypeEnum                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RegexpFlag                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | IDType                                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ArticleStatus                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EclassVersion                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EtimVersion                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ProfiClassVersion                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SyncItemStatus                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderCancelState                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderReturnEntryStatus                      | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | StockLevelStatus                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ReportTimeRange                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OneDayRange                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | RefreshTimeOption                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | changeType                                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OrderEntrySelectionStrategy                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | FactContextType                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ConverterType                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | QuoteAction                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | QuoteUserType                               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DiscountType                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SearchQueryContext                          | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | QuoteNotificationType                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CountryType                                 | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | B2BGroupEnum                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | B2BPermissionTypeEnum                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | MerchantCheckType                           | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | WorkflowTemplateType                        | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PermissionType                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | NotificationChannel                         | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CustomizationConversionOptions              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CustomerSegmentationConversionOptions       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SegmentConversionOptions                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | VariationConversionOptions                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | TriggerConversionOptions                    | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | EventType                                   | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CheckoutPciOptionEnum                       | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CheckoutFlowEnum                            | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | DocumentSort                                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | ItemInItemType                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PunchOutOrderOperationAllowed               | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | PunchOutClassificationDomain                | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | StockLevelAdjustmentReason                  | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | OData2webservicesFeatureTestPropertiesTypes | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | CartSourceType                              | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
EnumerationValue                | SwatchColorEnum                             | icon                | Media                                    | core                | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
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
ProductPromotion                | ProductPercentageDiscountPromotion          | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductBOGOFPromotion                       | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | AcceleratorProductBOGOFPromotion            | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductMultiBuyPromotion                    | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | AcceleratorProductMultiBuyPromotion         | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductSteppedMultiBuyPromotion             | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductBundlePromotion                      | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductPerfectPartnerPromotion              | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductOneToOnePerfectPartnerPromotion      | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductPerfectPartnerBundlePromotion        | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductPriceDiscountPromotionByPaymentType  | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
ProductPromotion                | ProductThresholdPriceDiscountPromotion      | productBanner       | Media                                    | promotions          | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | Principal                                   | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | User                                        | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | PrincipalGroup                              | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | UserGroup                                   | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | TestUserGroup                               | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | Company                                     | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | OrgUnit                                     | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | B2BUnit                                     | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | Employee                                    | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | BackofficeRole                              | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | CustomerList                                | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | StoreEmployeeGroup                          | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
Principal                       | B2BUserGroup                                | profilePicture      | Media                                    | comments            | 0 | 0 | 1 | 0 | 0 | 1 | 0 | 1
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

TODO
==
- example output/usage for files from `flexible`, `groovy` and `impex` folders
- ShowItem and ShowItemDirect working with SAP Cloud (instead of only MySQL like now)
- selenium scripts (already written, need only selenium installation instructions)

<details><summary>TODO: Selenium scripts, needs selenium installation instructions</summary>

## Import impex with media
Opens firefox or chrome (either with GUI or headless), logs into Backoffice/HMC and imports `media.impex`
with `media.zip`. This allows for importing multiple files (like images) into Hybris.<br/>
Shortcut: <b>I</b>mport <b>I</b>mpex with <b>M</b>edia <b>BO/HMC</b>:

```shell
iimbo path/to/media.impex path/to/media.zip
iimhmc path/to/media.impex path/to/media.zip
# TODO: test
```

## Update and initialize

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

</details>
