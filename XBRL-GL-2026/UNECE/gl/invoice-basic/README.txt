Selection profile: invoice-basic

This profile limits UNTDID 1001 Document name code to the subset:
  380, 381, 382, 383, 384

How to use from a business module (EE1):
- Set enum:domain   = cl1001:documentNameCodeDomain
- Set enum:linkrole = http://example.org/xbrl/gl/gen/untdid/1001/sel/invoice-basic/role/document-name-code

Then CSV values must be one of:
  cl1001:_380, cl1001:_381, cl1001:_382, cl1001:_383, cl1001:_384
