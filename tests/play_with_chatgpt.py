"""play with ChatGPT"""

# sourcery skip: avoid-global-variables
# pylint: disable=W0105
# noqa: E501

"""
In the following function, the function 'sf.s_get("mdf")' can return the type "Any" or "None".
The type of the variable 'mdf_i' is declared as 'cld.MetaAndDfs | None'.
In the line 'mdf_i: cld.MetaAndDfs | None = sf.s_get("mdf")' I get a warning by Pylance saying 
'Expression of type "Any | None" cannot be assigned to declared type "MetaAndDfs"
  Type "Any | None" cannot be assigned to type "MetaAndDfs"
    Type "None" cannot be assigned to type "MetaAndDfs"'
How can I cange the function 'mdf_from_excel_or_st()' to avoid this warning?
"""


def mdf_from_excel_or_st() -> cld.MetaAndDfs:
    """MDF aus Excel-Datei erzeugen oder aus session_state übernehmen"""

    mdf_i: cld.MetaAndDfs | None = sf.s_get("mdf")

    if mdf_i is not None and isinstance(mdf_i, cld.MetaAndDfs):
        logger.info("Excel-Datei schon importiert - mdf aus session_state übernommen")
    else:
        mdf_i: cld.MetaAndDfs = ex_in.import_prefab_excel(sf.s_get("f_up"))

    return mdf_i
