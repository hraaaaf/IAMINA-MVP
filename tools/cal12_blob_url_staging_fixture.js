/* CAL-12 / browser-ONLY Blob URL staging fixture.
 * Loaded into locally served test Chrome by Playwright, NOT by Flutter main,
 * NOT shipped with frontend/web. Fictitious one-page PDF bytes only.
 * URL.revokeObjectURL removes a handle, NOT OS caches/downloads/backups.
 */
(function () {
  'use strict';

  const host = window.location.hostname;
  if (host !== 'localhost' && host !== '127.0.0.1' && host !== '::1') {
    throw new Error('CAL12_FIXTURE_LOOPBACK_ONLY');
  }
  if (window.__cal12BlobStage) {
    throw new Error('CAL12_FIXTURE_DUPLICATE');
  }

  const allowedOwners = new Set(['fixture:vault:alpha', 'fixture:vault:beta']);
  const allowedDoctors = new Set(['fixture:doctor:one', 'fixture:doctor:two']);
  // Deliberately enumerable synthetic identities, NOT authentication credentials.
  const allowedSessions = new Map([
    ['fixture:session:alpha:1', 'fixture:vault:alpha'],
    ['fixture:session:beta:1', 'fixture:vault:beta'],
    ['fixture:session:alpha:2', 'fixture:vault:alpha'],
  ]);
  const prefix = 'CAL12-SYNTHETIC-FIXTURE:';
  const maxBytes = 262144;

  class FixtureBlobStage {
    constructor() {
      this._active = null;
      this._session = null;
      this._sessionGeneration = 0;
      this._timer = null;
      this._events = [];
      this._created = 0;
      this._revoked = 0;
      // A browser exit also revokes every handle held by this stage.
      window.addEventListener('pagehide', () => this.endSession('pagehide'));
    }

    get active() { return this._active !== null; }
    get metrics() {
      return Object.freeze({
        active: this.active,
        sessionActive: this._session !== null,
        created: this._created,
        revoked: this._revoked,
        eventReasons: this._events.map(e => e.reason),
      });
    }

    // A new instance invalidates every old grant, even for the SAME owner.
    // This is an in-memory test state machine; never substitute for IAMINA auth.
    beginSession(owner, sessionId) {
      this.endSession('session-rotation');
      if (allowedSessions.get(sessionId) !== owner) {
        throw new Error('CAL12_FIXTURE_SESSION_SCOPE');
      }
      const generation = ++this._sessionGeneration;
      this._session = {owner, sessionId, generation};
      return generation;
    }

    endSession(reason) {
      this.close(reason || 'logout');
      this._session = null;
    }

    _check(options) {
      const session = this._session;
      if (!session || !options ||
          options.owner !== session.owner ||
          options.sessionId !== session.sessionId ||
          options.sessionGeneration !== session.generation ||
          options.consentGeneration !== session.generation ||
          options.recipientGeneration !== session.generation) {
        throw new Error('CAL12_FIXTURE_SESSION');
      }
      if (!options || !(options.bytes instanceof Uint8Array)) {
        throw new Error('CAL12_FIXTURE_TYPE');
      }
      if (!allowedOwners.has(options.owner) ||
          !allowedOwners.has(options.reportOwner) ||
          options.owner !== options.reportOwner ||
          !allowedDoctors.has(options.recipient) ||
          !allowedDoctors.has(options.confirmedRecipient) ||
          options.recipient !== options.confirmedRecipient) {
        throw new Error('CAL12_FIXTURE_SCOPE');
      }
      if (options.mime !== 'application/pdf' ||
          options.channel !== 'local-preview' ||
          options.noticeVersion !== 'CAL12-DRAFT-2026-11-10.1' ||
          options.explicitConsent !== true) {
        throw new Error('CAL12_FIXTURE_CONSENT');
      }
      if (!Number.isSafeInteger(options.expiresAtMs) ||
          options.expiresAtMs <= Date.now() ||
          options.expiresAtMs > Date.now() + 15000) {
        throw new Error('CAL12_FIXTURE_EXPIRED');
      }
      if (options.bytes.length < 100 || options.bytes.length > maxBytes) {
        throw new Error('CAL12_FIXTURE_PDF_SIZE');
      }
      const head = new TextDecoder('latin1').decode(options.bytes.slice(0, 9));
      const tail = new TextDecoder('latin1').decode(
        options.bytes.slice(Math.max(0, options.bytes.length - 12)));
      const payload = new TextDecoder('latin1').decode(options.bytes);
      if (!head.startsWith('%PDF-1.') ||
          !tail.includes('%%EOF') ||
          !payload.includes(prefix + options.owner)) {
        throw new Error('CAL12_FIXTURE_PDF_PROVENANCE');
      }
    }

    open(options) {
      // Replacing a lease always closes the previous handle first, even if
      // the new request turns out invalid. A changed owner cannot inherit it.
      this.close('replacement');
      this._check(options);
      const disposable = Uint8Array.from(options.bytes);
      let url = null;
      try {
        const blob = new Blob([disposable], {type: 'application/pdf'});
        url = URL.createObjectURL(blob);
        this._active = {
          url, owner: options.owner, expiresAtMs: options.expiresAtMs,
          sessionGeneration: this._session.generation,
        };
        this._created += 1;
        this._timer = setTimeout(() => this.close('expiry'),
          Math.max(0, options.expiresAtMs - Date.now()));
        // This return value is a temporary local capability, NOT a share URL.
        return url;
      } catch (error) {
        if (url) URL.revokeObjectURL(url);
        this._active = null;
        throw error;
      } finally {
        disposable.fill(0);
      }
    }

    close(reason) {
      if (this._timer !== null) {
        clearTimeout(this._timer);
        this._timer = null;
      }
      const lease = this._active;
      this._active = null;
      if (!lease) return;
      // No public download, file picker, href, print or mail action.
      URL.revokeObjectURL(lease.url);
      this._revoked += 1;
      this._events.push({reason: String(reason || 'manual')});
    }

    revoke() { this.close('revoked'); }
    cancel() { this.close('cancelled'); }

    async useOnce(options, inspect) {
      if (typeof inspect !== 'function') {
        throw new Error('CAL12_FIXTURE_INSPECT_CALLBACK');
      }
      let url;
      try {
        url = this.open(options);
        await inspect(url);
        if (!this._active || this._active.url !== url ||
            !this._session ||
            this._session.generation !== this._active.sessionGeneration) {
          throw new Error('CAL12_FIXTURE_REVOKED_DURING_USE');
        }
        if (Date.now() >= this._active.expiresAtMs) {
          throw new Error('CAL12_FIXTURE_EXPIRED_DURING_USE');
        }
      } finally {
        this.close('finally');
      }
    }
  }

  Object.defineProperty(window, '__cal12BlobStage', {
    value: new FixtureBlobStage(),
    writable: false, enumerable: false, configurable: false,
  });
})();
