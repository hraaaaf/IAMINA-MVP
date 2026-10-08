/// Exact fail-closed replies from the older certified backend release.
///
/// Compatibility only: these static strings identify an already blocked
/// external provider. They never authorize an AI request or transfer data.
const Set<String> _legacyGovernanceReplies = {
  'Je peux continuer avec les fonctions locales d’IAMINA. Demande-moi une donnée précise enregistrée — '
      'glycémie, repas, sommeil, stress, traitement enregistré, CGM ou documents — '
      'ou demande-moi ce que je sais faire.',
  "I can keep helping with IAmina's local functions. Ask me for a specific recorded item — "
      'glucose, meals, sleep, stress, recorded treatment, CGM or documents — '
      'or ask what I can do.',
  'نقدر نكمل معك بوظائف IAmina المحلية. اسألني عن معلومة محددة ومسجلة مثل السكر، الوجبات، '
      'النوم، التوتر، العلاج المسجل، CGM أو الوثائق، أو اسألني ماذا أستطيع أن أفعل.',
  'N9der nkemmel m3ak b fonctions locales dyal IAmina. Sowlni 3la data m7edda msjla — '
      'sucre, makla, n3as, stress, traitement msjjel, CGM wela documents — '
      'wela sowlni chno n9der ndir.',
};

bool isLegacyGovernanceFallback(String reply) =>
    _legacyGovernanceReplies.contains(reply.trim());
