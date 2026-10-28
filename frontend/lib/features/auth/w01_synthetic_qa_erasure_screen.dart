import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:provider/provider.dart';

import '../../data/drift/database.dart';
import '../../services/auth_service.dart';
import '../../services/consent_evidence_store.dart';

/// Emergency synthetic-only QA cleanup path.
/// This route intentionally renders NO clinical content and is available before
/// app-lock/onboarding ONLY on a verified, SSO-protected Preview Web origin.
/// The AuthService repeats all scope guards and the server checks bearer and
/// exact synthetic email before accepting DELETE /account.
class W01SyntheticQaErasureScreen extends StatefulWidget {
  const W01SyntheticQaErasureScreen({super.key});

  @override
  State<W01SyntheticQaErasureScreen> createState() =>
      _W01SyntheticQaErasureScreenState();
}

class _W01SyntheticQaErasureScreenState
    extends State<W01SyntheticQaErasureScreen> {
  bool _busy = false;
  String? _error;

  Future<void> _erase() async {
    if (_busy) return;
    final auth = context.read<AuthService>();
    if (!auth.canEraseSyntheticPreviewAccount) return;

    final controller = TextEditingController();
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Delete synthetic QA account'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text(
              'Preview test only. This permanently deletes the account and '
              'its test data through IAMINA. Type DELETE MY ACCOUNT.',
            ),
            const SizedBox(height: 14),
            TextField(
              key: const Key('w01-qa-cleanup-confirmation'),
              controller: controller,
              decoration: const InputDecoration(
                labelText: 'DELETE MY ACCOUNT',
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancel'),
          ),
          FilledButton(
            key: const Key('w01-qa-cleanup-submit'),
            onPressed: () => Navigator.pop(
              dialogContext, controller.text == 'DELETE MY ACCOUNT'),
            child: const Text('Delete test account'),
          ),
        ],
      ),
    );
    controller.dispose();
    if (confirmed != true || !mounted ||
        !auth.canEraseSyntheticPreviewAccount) return;

    final db = context.read<AppDatabase>();
    final evidence = context.read<ConsentEvidenceStore>();
    final router = GoRouter.of(context);
    setState(() { _busy = true; _error = null; });
    try {
      await auth.eraseSyntheticPreviewAccount(
        purgeLocalVault: () async {
          await db.purgeSyntheticPatientVaultAfterRemoteErasure();
          await evidence.clear();
        },
      );
      router.go('/login');
    } catch (_) {
      if (!mounted) return;
      if (!auth.hasRemoteApiCredential) {
        router.go('/login');
      } else {
        setState(() => _error =
            'Deletion unconfirmed. Session preserved. Do not create '
            'another account; retry or request a manual review.');
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthService>();
    if (!auth.canEraseSyntheticPreviewAccount) {
      return const Scaffold(body: Center(
        child: Text('Synthetic QA cleanup unavailable'),
      ));
    }
    return Scaffold(
      appBar: AppBar(title: const Text('IAMINA · Synthetic QA cleanup')),
      body: Center(
        child: ConstrainedBox(
          constraints: const BoxConstraints(maxWidth: 560),
          child: Padding(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                const Icon(Icons.verified_user_outlined, size: 42),
                const SizedBox(height: 16),
                const Text(
                  'Only test accounts @example.invalid can be deleted. '
                  'This page does not open the medical record.',
                  textAlign: TextAlign.center,
                ),
                if (_error != null) ...[
                  const SizedBox(height: 14),
                  Text(_error!, key: const Key('w01-qa-cleanup-error')),
                ],
                const SizedBox(height: 20),
                FilledButton.icon(
                  key: const Key('w01-qa-cleanup-start'),
                  onPressed: _busy ? null : _erase,
                  icon: const Icon(Icons.delete_forever_outlined),
                  label: Text(_busy
                      ? 'Deleting synthetic account…'
                      : 'Delete synthetic test account'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
