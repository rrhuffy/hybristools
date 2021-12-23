// xg $PROJECTS_DIR/hybristools/groovy/printCMSPageSlotComponentStructure.groovy | treepywithoutcolor
catalogVersionStaged = catalogVersionService.getCatalogVersion("powertoolsContentCatalog","Staged");
pages = defaultCMSAdminPageService.getAllPagesForCatalogVersionAndPageStatuses(catalogVersionStaged, Arrays.asList(de.hybris.platform.cms2.enums.CmsPageStatus.ACTIVE));
site = defaultCMSAdminSiteService.getSiteForId("powertools");
sessionService.setAttribute("activeCatalogVersion", catalogVersionStaged.getPk());
sessionService.setAttribute("activeSite", site.getPk());

pages.each { page -> 
    defaultCMSAdminContentSlotService.getContentSlotsForPage(page).each { slot -> 
        slot.getCMSComponents().each { component -> 
            println page.getUid() + "_" + page.getMasterTemplate().getUid() + "/" + slot.getUid() + "/" + component.getUid()
        }
    }
}

null
