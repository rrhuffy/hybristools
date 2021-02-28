typeManager = de.hybris.platform.jalo.type.TypeManager.getInstance()

(typeManager.getType('$1').allSubTypes + typeManager.getType('$1'))
.stream()
.map({itemType ->
    typeManager.getType(itemType.code).allSuperTypes
    .stream()
    .map({superType -> superType.code})
    .collect()
    .reverse()
    .join('/') + '/' + itemType.code
})
.collect()
.join('\n')