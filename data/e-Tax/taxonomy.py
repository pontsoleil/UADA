import os
import csv

DEBUG = True
TRACE = True
SEP = os.sep
base_dir = "data/e-Tax"
bs_file_name = "BS_10.csv"
pl_file_name = "PL_10.csv"
bs_data_file_name = "HOT010_3.0_BS_10.csv"
pl_data_file_name = "HOT010_3.0_PL_10.csv"
namespace = "xbrl-etax"
out = "etax"
core_xsd = f"{out}.xsd"
out_lbl = f"{out}_lbl"
out_pre = f"{out}_pre"
lang = "ja"

etaxDict = {}
records = []


def file_path(pathname):
    if SEP == pathname[0:1]:
        return pathname
    else:
        pathname = pathname.replace("/", SEP)
        dir = os.path.dirname(__file__)
        new_path = os.path.join(dir, pathname)
        return new_path


def csv_to_dict_list(file_path, encoding="utf-8-sig"):
    """CSVファイルを辞書のリストとして読み込む"""
    with open(file_path, mode="r", encoding=encoding) as file:
        reader = csv.DictReader(file)  # 先頭行をキーとして辞書を作成
        data_list = [row for row in reader]  # 各行を辞書のリストとして格納
    return data_list


def defineElement(cor_id, record):
    global lines
    global elementsDefined
    if not cor_id in elementsDefined:
        elementsDefined.add(cor_id)
        if not record:
            print(f"NOT DEFINED {cor_id} record")
            return
        propertyType = record["type"]
        if record["semanticPath"].endswith("Amount.Value"):
            type = "cor:amountType"
        else:
            type = (
                record["datatype"]
                if "datatype" in record and record["datatype"]
                else ""
            )
        schema_id = getSchemaID(cor_id)
        if DEBUG:
            print(f"define {cor_id} {schema_id} [{propertyType}]")
        if propertyType.lower().endswith(
            "class"
        ):  # or cor_id in targetRefDict or cor_id in referenceDict:
            line = f'\t<element name="{schema_id}" id="{schema_id}" abstract="true" type="xbrli:stringItemType" nillable="true" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        else:
            type = "xbrli:monetaryItemType"
            line = f'\t<element name="{schema_id}" id="{schema_id}" type="{type}" nillable="false" substitutionGroup="xbrli:item" xbrli:periodType="instant"/>\n'
        lines.append(line)


def linkLabel(cor_id, name, desc, lang):
    global locsDefined
    global definedLabels
    global arcsDefined
    global definedDescs
    global definedDescArcs
    # name
    schema_id = getSchemaID(cor_id)
    if name:
        lines.append(f"\t\t<!-- {cor_id} {name} -->\n")
        if not cor_id in locsDefined:
            locsDefined[cor_id] = cor_id
            line = f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:loc defined -->\n"
        lines.append(line)
        # name
        if not cor_id in definedLabels:
            definedLabels[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="label_{schema_id}" xlink:title="label_{schema_id}" id="label_{schema_id}" xml:lang="{lang}" xlink:role="http://www.xbrl.org/2003/role/label">{name}</link:label>\n'
        else:
            line = f"\t\t\t<!-- link:label http://www.xbrl.org/2003/role/label defined -->\n"
        lines.append(line)
        if not cor_id in arcsDefined:
            arcsDefined[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/concept-label" xlink:from="{schema_id}" xlink:to="label_{schema_id}" xlink:title="label: {schema_id} to label_{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:labelArc http://www.xbrl.org/2003/arcrole/concept-label defined -->\n"
        lines.append(line)
    # desc
    if desc:  # and name != desc:
        if not cor_id in definedDescs:
            definedDescs[cor_id] = cor_id
            line = f'\t\t<link:label xlink:type="resource" xlink:label="description_{schema_id}" xlink:title="description_{schema_id}" id="description_{schema_id}" xml:lang="{lang}" xlink:role="{namespace}/role/description">{desc}</link:label>\n'
        else:
            line = f"\t\t\t<!-- link:label {namespace}/role/description defined -->\n"
        lines.append(line)
        if not cor_id in definedDescArcs:
            definedDescArcs[cor_id] = cor_id
            line = f'\t\t<link:labelArc xlink:type="arc" xlink:arcrole="{namespace}/arcrole/concept-description" xlink:from="{schema_id}" xlink:to="description_{schema_id}" xlink:title="label: {cor_id} to label_{schema_id}"/>\n'
        else:
            line = f"\t\t\t<!-- link:labelArc {namespace}/arcrole/concept-description defined -->\n"
        lines.append(line)


def getRecord():
    return


def getSchemaID():
    return


def linkPresentation(cor_id, children, n):
    global lines
    global count
    global locsDefined
    global arcsDefined
    if not cor_id:
        return
    record = getRecord(cor_id)
    schema_id = getSchemaID(cor_id)
    if not record:
        return
    propertyType = record["type"]
    name = record["name"]
    if not cor_id in locsDefined:
        locsDefined[cor_id] = name
        lines.append(f"\t\t<!-- {propertyType} {schema_id} {name} -->\n")
        lines.append(
            f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{schema_id}" xlink:label="{schema_id}" xlink:title="presentation: {schema_id} {name}"/>\n'
        )
    for child_id in children:
        child_abbreviation = getSchemaID(child_id)
        child = getRecord(child_id)
        child_property = child["type"]
        child_name = child["name"]
        if child_property.lower().endswith("class"):
            target_id = child_id
            target_abbreviation = child_abbreviation
            if not target_id in locsDefined:
                locsDefined[target_id] = child_name
                lines.append(
                    f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{target_abbreviation}" xlink:label="{target_abbreviation}" xlink:title="presentation parent: {target_abbreviation} {child_name}"/>\n'
                )
            arc_id = f"{cor_id} {target_id}"
            if not arc_id in arcsDefined and cor_id != target_id:
                arcsDefined[arc_id] = f"{name} to {child_name}"
                count += 1
                lines.append(
                    f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{schema_id}" xlink:to="{target_abbreviation}" order="{count}" xlink:title="presentation: {schema_id} {name} to {target_abbreviation} {child_name}"/>\n'
                )
                if "children_pre" in child and len(child["children_pre"]) > 0:
                    grand_children = child["children_pre"]
                    linkPresentation(target_id, grand_children, n + 1)
        else:
            if not child_id in locsDefined:
                locsDefined[child_id] = child_name
                lines.append(
                    f'\t\t<link:loc xlink:type="locator" xlink:href="{core_xsd}#{child_abbreviation}" xlink:label="{child_abbreviation}" xlink:title="presentation parent: {child_abbreviation} {child_name}"/>\n'
                )
            arc_id = f"{cor_id} {child_id}"
            if not arc_id in arcsDefined and cor_id != child_id:
                arcsDefined[arc_id] = f"{name} to {child_name}"
                count += 1
                lines.append(
                    f'\t\t<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="{schema_id}" xlink:to="{child_abbreviation}" order="{count}" xlink:title="presentation: {schema_id} {name} to {child_abbreviation} {child_name}"/>\n'
                )
                if "children_pre" in child and len(child["children_pre"]) > 0:
                    grand_children = child["children_pre"]
                    linkPresentation(child_id, grand_children, n + 1)
    children = None


if __name__ == "__main__":
    bs_dict_list = csv_to_dict_list(f"{base_dir}/{bs_file_name}")
    pl_dict_list = csv_to_dict_list(f"{base_dir}/{pl_file_name}")
    bs_data_dict_list = csv_to_dict_list(f"{base_dir}/{bs_data_file_name}")
    pl_data_dict_list = csv_to_dict_list(f"{base_dir}/{pl_data_file_name}")
    bs_dict = {d["Ledger_Account_Number"]: d for d in bs_dict_list}
    pl_dict = {d["Ledger_Account_Number"]: d for d in pl_dict_list}

    ###################################
    #   presentationLink
    #
    locsDefined = {}
    arcsDefined = {}
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xbrli="http://www.xbrl.org/2003/instance">\n',
        '  <link:roleRef roleURI="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedBalanceSheets" xlink:type="simple" xlink:href="http://xml.e-tax.nta.go.jp/jp/fr/etax/o/rt/2013-03-25/jpfr-etax-rt-2013-03-25.xsd#NonConsolidatedBalanceSheets" />\n',
        '  <link:roleRef roleURI="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedStatementsOfIncome" xlink:type="simple" xlink:href="http://xml.e-tax.nta.go.jp/jp/fr/etax/o/rt/2013-03-25/jpfr-etax-rt-2013-03-25.xsd#NonConsolidatedStatementsOfIncome" />\n',
        '  <link:roleRef roleURI="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedStatementsOfChangesInNetAssets" xlink:type="simple" xlink:href="http://xml.e-tax.nta.go.jp/jp/fr/etax/o/rt/2013-03-25/jpfr-etax-rt-2013-03-25.xsd#NonConsolidatedStatementsOfChangesInNetAssets" />\n',
        '  <link:presentationLink xlink:type="extended" xlink:role="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedBalanceSheets">\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CurrentAssetsAbstract" xlink:label="CurrentAssetsAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ElectronicallyRecordedMonetaryClaimsOperatingCA" xlink:label="ElectronicallyRecordedMonetaryClaimsOperatingCA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CurrentAssetsAbstract" xlink:to="ElectronicallyRecordedMonetaryClaimsOperatingCA" order="6.5" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_AllowanceCurrentAssetsAbstract" xlink:label="AllowanceCurrentAssetsAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CurrentAssetsAbstract" xlink:to="AllowanceCurrentAssetsAbstract" order="20.022" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_AllowanceForDoubtfulAccountsCA" xlink:label="AllowanceForDoubtfulAccountsCA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="AllowanceCurrentAssetsAbstract" xlink:to="AllowanceForDoubtfulAccountsCA" order="1.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherIntangibleAssetsIAAbstract" xlink:label="OtherIntangibleAssetsIAAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_IntangibleAssetsAbstract" xlink:label="IntangibleAssetsAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="IntangibleAssetsAbstract" xlink:to="OtherIntangibleAssetsIAAbstract" order="10.01" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_TelephoneSubscriptionRight" xlink:label="TelephoneSubscriptionRight" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherIntangibleAssetsIAAbstract" xlink:to="TelephoneSubscriptionRight" order="2.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherLongTermAssetsIOAAbstract" xlink:label="OtherLongTermAssetsIOAAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_InvestmentsAndOtherAssetsAbstract" xlink:label="InvestmentsAndOtherAssetsAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="InvestmentsAndOtherAssetsAbstract" xlink:to="OtherLongTermAssetsIOAAbstract" order="25.051" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_InsuranceFunds" xlink:label="InsuranceFunds" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherLongTermAssetsIOAAbstract" xlink:to="InsuranceFunds" order="15.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GuaranteeDepositsIOA" xlink:label="GuaranteeDepositsIOA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherLongTermAssetsIOAAbstract" xlink:to="GuaranteeDepositsIOA" order="19.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_LeaseDepositsIOA" xlink:label="LeaseDepositsIOA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherLongTermAssetsIOAAbstract" xlink:to="LeaseDepositsIOA" order="21.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ProvisionCLAbstract" xlink:label="ProvisionCLAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ProvisionForBonuses" xlink:label="ProvisionForBonuses" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="ProvisionCLAbstract" xlink:to="ProvisionForBonuses" order="3.081" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherProvisionCL" xlink:label="OtherProvisionCL" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="ProvisionCLAbstract" xlink:to="OtherProvisionCL" order="3.21" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_AccountsPayableOrdinaryTransactionsPaidInShortTermCLAbstract" xlink:label="AccountsPayableOrdinaryTransactionsPaidInShortTermCLAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CurrentLiabilitiesAbstract" xlink:label="CurrentLiabilitiesAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CurrentLiabilitiesAbstract" xlink:to="AccountsPayableOrdinaryTransactionsPaidInShortTermCLAbstract" order="14.0313" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_AccruedBusinessOfficeTaxes" xlink:label="AccruedBusinessOfficeTaxes" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="AccountsPayableOrdinaryTransactionsPaidInShortTermCLAbstract" xlink:to="AccruedBusinessOfficeTaxes" order="3.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_AccruedConsumptionTaxes" xlink:label="AccruedConsumptionTaxes" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="AccountsPayableOrdinaryTransactionsPaidInShortTermCLAbstract" xlink:to="AccruedConsumptionTaxes" order="4.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherLiabilitiesPayableWithinOneYearAbstract" xlink:label="OtherLiabilitiesPayableWithinOneYearAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CurrentLiabilitiesAbstract" xlink:to="OtherLiabilitiesPayableWithinOneYearAbstract" order="14.0314" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_SuspenseReceiptOfConsumptionTaxes" xlink:label="SuspenseReceiptOfConsumptionTaxes" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherLiabilitiesPayableWithinOneYearAbstract" xlink:to="SuspenseReceiptOfConsumptionTaxes" order="14.0" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherRetainedEarningsAbstract" xlink:label="OtherRetainedEarningsAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserve" xlink:label="GeneralReserve" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherRetainedEarningsAbstract" xlink:to="GeneralReserve" order="0.1934" />\n',
        "  </link:presentationLink>\n",
        '  <link:presentationLink xlink:type="extended" xlink:role="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedStatementsOfIncome">\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_NetSalesAbstract" xlink:label="NetSalesAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_NetSales" xlink:label="NetSales" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="NetSalesAbstract" xlink:to="NetSales" order="18.01" preferredLabel="http://www.xbrl.org/2003/role/totalLabel" />\n',
        "    <!-- XBRL japan addition start 2025-03-08 -->\n",
        '    <link:loc xlink:type="locator" xlink:href="XBRL-etax.xsd#etax_NetSalesFromElectricTransaction" xlink:label="NetSalesFromElectricTransaction" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="NetSales" xlink:to="NetSalesFromElectricTransaction" order="18.02" />\n',
        '    <link:loc xlink:type="locator" xlink:href="XBRL-etax.xsd#etax_NetSalesFromTraditionalTransaction" xlink:label="NetSalesFromTraditionalTransaction" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="NetSales" xlink:to="NetSalesFromTraditionalTransaction" order="18.03"/>\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CostOfGoodsSold" xlink:label="CostOfGoodsSold" />\n',
        '    <link:loc xlink:type="locator" xlink:href="XBRL-etax.xsd#etax_CostOfGoodsSoldFromElectricTransaction" xlink:label="CostOfGoodsSoldFromElectricTransaction" />\n',
        '	<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CostOfGoodsSold" xlink:to="CostOfGoodsSoldFromElectricTransaction" order="18.03"/>\n',
        '    <link:loc xlink:type="locator" xlink:href="XBRL-etax.xsd#etax_CostOfGoodsSoldFromTraditionalTransaction" xlink:label="CostOfGoodsSoldFromTraditionalTransaction" />\n',
        '	<link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CostOfGoodsSold" xlink:to="CostOfGoodsSoldFromTraditionalTransaction" order="18.03"/>\n',
        "    <!-- XBRL japan addition end 2025-03-08-->\n",
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CostOfGoodsSoldAbstract" xlink:label="CostOfGoodsSoldAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_PurchaseAllowanceAndReturns" xlink:label="PurchaseAllowanceAndReturns" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="CostOfGoodsSoldAbstract" xlink:to="PurchaseAllowanceAndReturns" order="1.01" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_SellingGeneralAndAdministrativeExpensesAbstract" xlink:label="SellingGeneralAndAdministrativeExpensesAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherSalariesSGA" xlink:label="OtherSalariesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="OtherSalariesSGA" order="24.011" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_LegalWelfareExpensesSGA" xlink:label="LegalWelfareExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="LegalWelfareExpensesSGA" order="24.012" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CompensationsSGA" xlink:label="CompensationsSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="CompensationsSGA" order="25.003" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_CommissionFeeSGA" xlink:label="CommissionFeeSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="CommissionFeeSGA" order="25.008" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_RentsSGA" xlink:label="RentsSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="RentsSGA" order="25.01" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_RepairAndMaintenanceSGA" xlink:label="RepairAndMaintenanceSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="RepairAndMaintenanceSGA" order="25.012" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_UtilitiesExpensesSGA" xlink:label="UtilitiesExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="UtilitiesExpensesSGA" order="25.015" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OfficeSuppliesExpensesSGA" xlink:label="OfficeSuppliesExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="OfficeSuppliesExpensesSGA" order="25.017" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_VehicleExpensesSGA" xlink:label="VehicleExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="VehicleExpensesSGA" order="25.018" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ConferenceExpensesSGA" xlink:label="ConferenceExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="ConferenceExpensesSGA" order="25.019" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_MembershipFeeSGA" xlink:label="MembershipFeeSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="MembershipFeeSGA" order="25.02" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_TravelingAndTransportationExpensesSGA" xlink:label="TravelingAndTransportationExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="TravelingAndTransportationExpensesSGA" order="25.022" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_MiscellaneousExpensesSGA" xlink:label="MiscellaneousExpensesSGA" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="SellingGeneralAndAdministrativeExpensesAbstract" xlink:to="MiscellaneousExpensesSGA" order="25.024" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_NonOperatingIncomeAbstract" xlink:label="NonOperatingIncomeAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_MiscellaneousIncomeNOI" xlink:label="MiscellaneousIncomeNOI" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="NonOperatingIncomeAbstract" xlink:to="MiscellaneousIncomeNOI" order="5.061" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ExtraordinaryIncomeAbstract" xlink:label="ExtraordinaryIncomeAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GainOnSalesOfInvestmentSecuritiesEI" xlink:label="GainOnSalesOfInvestmentSecuritiesEI" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="ExtraordinaryIncomeAbstract" xlink:to="GainOnSalesOfInvestmentSecuritiesEI" order="2.001" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_ExtraordinaryLossAbstract" xlink:label="ExtraordinaryLossAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_LossOnSalesOfInvestmentSecuritiesEL" xlink:label="LossOnSalesOfInvestmentSecuritiesEL" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="ExtraordinaryLossAbstract" xlink:to="LossOnSalesOfInvestmentSecuritiesEL" order="4.0002" />\n',
        "  </link:presentationLink>\n",
        '  <!--<link:presentationLink xlink:type="extended" xlink:role="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedStatementsOfChangesInNetAssets">\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserveSSAbstract" xlink:label="GeneralReserveSSAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherRetainedEarningsSSAbstract" xlink:label="OtherRetainedEarningsSSAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherRetainedEarningsSSAbstract" xlink:to="GeneralReserveSSAbstract" order="18.08" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserve" xlink:label="GeneralReserve" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="GeneralReserveSSAbstract" xlink:to="GeneralReserve" order="0" preferredLabel="http://www.xbrl.org/2003/role/periodStartLabel" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserve" xlink:label="GeneralReserve" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="GeneralReserveSSAbstract" xlink:to="GeneralReserve" order="3" preferredLabel="http://www.xbrl.org/2003/role/periodEndLabel" />\n',
        "  </link:presentationLink>-->\n",
        '  <link:presentationLink xlink:type="extended" xlink:role="http://xml.e-tax.nta.go.jp/jp/fr/etax/role/NonConsolidatedStatementsOfChangesInNetAssets">\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserveSSAbstract" xlink:label="GeneralReserveSSAbstract" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_OtherRetainedEarningsSSAbstract" xlink:label="OtherRetainedEarningsSSAbstract" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="OtherRetainedEarningsSSAbstract" xlink:to="GeneralReserveSSAbstract" order="18.08" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserve" xlink:label="GeneralReserveStart" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="GeneralReserveSSAbstract" xlink:to="GeneralReserveStart" order="0" preferredLabel="http://www.xbrl.org/2003/role/periodStartLabel" />\n',
        '    <link:loc xlink:type="locator" xlink:href="http://info.edinet-fsa.go.jp/jp/fr/gaap/t/cte/2012-01-25/jpfr-t-cte-2012-01-25.xsd#jpfr-t-cte_GeneralReserve" xlink:label="GeneralReserveEnd" />\n',
        '    <link:presentationArc xlink:type="arc" xlink:arcrole="http://www.xbrl.org/2003/arcrole/parent-child" xlink:from="GeneralReserveSSAbstract" xlink:to="GeneralReserveEnd" order="3" preferredLabel="http://www.xbrl.org/2003/role/periodEndLabel" />\n',
        '  </link:presentationLink>\n',
        '</link:linkbase>\n',
    ]
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        "<!--  (c) 2025 XBRL Japan inc. -->\n",
        "<link:linkbase\n",
        '\txmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n',
        '\txsi:schemaLocation="http://www.xbrl.org/2003/linkbase http://www.xbrl.org/2003/xbrl-linkbase-2003-12-31.xsd"\n',
        '\txmlns:link="http://www.xbrl.org/2003/linkbase"\n',
        '\txmlns:xlink="http://www.w3.org/1999/xlink">\n',
        f'\t<link:roleRef roleURI="{namespace}/role" xlink:type="simple" xlink:href="{core_xsd}#core-role"/>\n',
        f'\t<link:presentationLink xlink:type="extended" xlink:role="{namespace}/role">\n',
    ]
    locsDefined = {}
    arcsDefined = {}
    class_records = [x for x in records if "C" == x["type"]]
    for record in class_records:
        cor_id = record["cor_id"]
        propertyType = record["type"]
        count = 0
        children = record["children_pre"]
        linkPresentation(cor_id, children, 1)

    lines.append("\t</link:presentationLink>\n")
    lines.append("</link:linkbase>\n")

    cor_presentation_file = file_path(f"{base_dir}/{out_pre}.xml")
    with open(cor_presentation_file, "w", encoding="utf-8-sig", newline="") as f:
        f.writelines(lines)
    if TRACE:
        print(f"-- {cor_presentation_file}")
