// xg $PROJECTS_DIR/hybristools/groovy/getUsersOfUserGroup.groovy --parameters admingroup
def getUsersOfUserGroup(String userGroupUid) {
    Set output = []
    userService.getUserGroupForUID(userGroupUid).getMembers().each { principal ->
        if (principal instanceof de.hybris.platform.core.model.user.UserModel) {
            output.add(principal);
        }
        else if (principal instanceof de.hybris.platform.core.model.user.UserGroupModel) {
            output.addAll(getUsersOfUserGroup(principal.getUid()));
        }
    }
    return output;
}

userGroup = '''$1'''
if (userGroup.equals('$' + '1')) {
    println "You must provide 1 argument: UserGroup's uid"
    return
}

getUsersOfUserGroup(userGroup).sort { it.uid.toLowerCase() }.each { println "$it.uid" }
null // avoid printing output and result when using execute_script.py
