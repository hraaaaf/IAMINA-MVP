// Fail closed on substitutions or dropped/extra numbers and units; raw OCR text never enters reports.
export function normalizeDigits(value) {
  return [...value].map(char => {
    const cp = char.codePointAt(0);
    if (cp >= 0x0660 && cp <= 0x0669) return String(cp - 0x0660);
    if (cp >= 0x06f0 && cp <= 0x06f9) return String(cp - 0x06f0);
    return char;
  }).join('');
}

export function numericTokens(text) {
  const re = /(?<![\p{L}\p{N}])[0-9]+(?:[.,][0-9]+)?(?![\p{L}\p{N}])/gu;
  return [...normalizeDigits(text || '').matchAll(re)].map(x => x[0].replace(',', '.'));
}

export function unitTokens(text) {
  const re = /(?:µ\s*mol\s*\/\s*l|mmol\s*\/\s*l|mg\s*\/\s*d\s*l|g\s*\/\s*l|%)/gu;
  return [...(text || '').replace(/μ/g,'µ').toLowerCase().matchAll(re)].map(x=>x[0].replace(/\s+/g,''));
}

const frequency = xs => { const m=new Map(); for(const x of xs) m.set(x,(m.get(x)||0)+1); return m; };
export function compareSetsExact(expected,actual) {
  const a=frequency(expected),b=frequency(actual);
  return a.size===b.size && [...a].every(([key,count])=>b.get(key)===count);
}

// This strict synthetic benchmark refuses a right set of numbers on wrong rows.
// Exact clinical field/source provenance requires a separate human qualification.
export function sourceRowsExact(expectedLines, extracted) {
  if (!Array.isArray(expectedLines) || expectedLines.length === 0) return false;
  const row = value => normalizeDigits(String(value).normalize('NFC'))
    .toLocaleLowerCase('und').replace(/\s+/gu, '').replace(/(\d),(\d)/gu, '$1.$2');
  const expected = expectedLines.map(row);
  const actual = String(extracted || '').split(/\r?\n/).map(row).filter(Boolean);
  const count = values => values.reduce((map,value) =>
    map.set(value,(map.get(value)||0)+1),new Map());
  const observed = count(actual);
  return [...count(expected)].every(([value,n]) => (observed.get(value)||0) >= n);
}

export function scoreTranscription(info,extracted) {
  const actualNumbers=numericTokens(extracted),actualUnits=unitTokens(extracted);
  const labels=info.expectedLabels||[];
  const s=(extracted||'').normalize('NFC').toLocaleLowerCase('und');
  const labelsExact=labels.every(label=>s.includes(label.normalize('NFC').toLocaleLowerCase('und')));
  const numericExact=compareSetsExact(info.expectedNumbers,actualNumbers);
  const unitsExact=compareSetsExact(info.expectedUnits,actualUnits);
  const rowBindingsExact=sourceRowsExact(info.expectedLines,extracted);
  return {
    caseId:info.id,numericExact,unitsExact,labelsExact,rowBindingsExact,
    safeForReview:numericExact&&unitsExact&&labelsExact&&rowBindingsExact,
    expectedNumericCount:info.expectedNumbers.length,extractedNumericCount:actualNumbers.length,
    expectedUnitCount:info.expectedUnits.length,extractedUnitCount:actualUnits.length,
    expectedLabelCount:labels.length
  };
}
