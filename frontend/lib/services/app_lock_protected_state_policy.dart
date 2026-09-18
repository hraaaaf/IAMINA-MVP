bool authSessionCountsAsProtectedLocalState({
  required bool auditAllowed,
  required bool isAuthenticated,
  required bool hasRemoteApiCredential,
}) {
  if (auditAllowed || !isAuthenticated) return false;

  // A hosted/native bearer proves the remote account session, not that this
  // browser previously configured IAmina's device-local app lock.
  return !hasRemoteApiCredential;
}
