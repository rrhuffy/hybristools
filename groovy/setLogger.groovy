// xg $PROJECTS_DIR/hybristools/groovy/setLogger.groovy
// This groovy script is useful in Hybris 6.0 (and probably 6.1) where new log4j2 was introduced, but you couldn't add
// new logger in HAC, you can only edit existing logger. IIRC 6.2 added a way to add a new logger in HAC so in 6.2+ you
// should (but this script is still working in for example 2005) just use src/set_logger_level.py by using shortcut:
// sl de.hybris.platform.jalo.flexiblesearch.FlexibleSearch DEBUG

import org.apache.logging.log4j.LogManager
import org.apache.logging.log4j.core.config.LoggerConfig
import org.apache.logging.log4j.Level

loggerName = "de.hybris.platform.jalo.flexiblesearch.FlexibleSearch"
logLevel = "DEBUG"

loggingContext = LogManager.getContext(false)
loggingConfig = loggingContext.getConfiguration()
specificConfig = loggingConfig.getLoggers().get(loggerName)
if (specificConfig == null) {
    specificConfig = new LoggerConfig(loggerName, Level.getLevel(logLevel), true)
    loggingConfig.addLogger(loggerName, specificConfig)
} else {
    specificConfig.setLevel(Level.getLevel(logLevel))
}
loggingContext.updateLoggers()
null // avoid printing output and result when using execute_script.py