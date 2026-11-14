import 'package:flutter/material.dart';

/// D2 preparation only: an isolated, non-persistent visitor presentation.
///
/// This is deliberately NOT mounted in the clinical application bootstrap.
/// No AppDatabase, AuthService, SyncService, ApiClient or AI service is created
/// or read here. The parent owns the future authentication hand-off.
class D2GuestShell extends StatefulWidget {
  const D2GuestShell({
    super.key,
    required this.onProtectedAction,
  });

  /// Receives only a route/intention. Never receives or stores patient data.
  final ValueChanged<String> onProtectedAction;

  @override
  State<D2GuestShell> createState() => _D2GuestShellState();
}

class _D2Destination {
  const _D2Destination(this.id, this.icon, this.fr, this.en, this.ar);

  final String id;
  final IconData icon;
  final String fr;
  final String en;
  final String ar;
}

class _D2Action {
  const _D2Action(this.id, this.route, this.icon, this.fr, this.en, this.ar);

  final String id;
  final String route;
  final IconData icon;
  final String fr;
  final String en;
  final String ar;
}

const _destinations = <_D2Destination>[
  _D2Destination('dashboard', Icons.home_outlined, 'Accueil', 'Home', 'الرئيسية'),
  _D2Destination('journal', Icons.show_chart, 'Mesures', 'Measurements', 'القياسات'),
  _D2Destination('summary', Icons.description_outlined, 'Rapports', 'Reports', 'التقارير'),
  _D2Destination('profile', Icons.person_outline, 'Profil', 'Profile', 'الملف الشخصي'),
];

const _guestActions = <String, List<_D2Action>>{
  'dashboard': [
    _D2Action('add', '/ajouter', Icons.add, 'Ajouter une mesure',
        'Add a measurement', 'إضافة قياس'),
    _D2Action('import', '/importer', Icons.upload_file_outlined,
        'Importer un document', 'Import a document', 'استيراد مستند'),
    _D2Action('companion', '/companion/chat', Icons.chat_bubble_outline,
        'Parler avec IAMINA', 'Talk to IAMINA', 'التحدث مع أمينة'),
  ],
  'journal': [
    _D2Action('add', '/ajouter', Icons.add, 'Ajouter une mesure',
        'Add a measurement', 'إضافة قياس'),
  ],
  'summary': [
    _D2Action('export', '/summary?intent=export', Icons.download_outlined,
        'Exporter mes données', 'Export my data', 'تصدير بياناتي'),
  ],
  'profile': [
    _D2Action('edit', '/profile?intent=edit', Icons.edit_outlined,
        'Modifier mon profil', 'Edit my profile', 'تعديل ملفي الشخصي'),
  ],
};

String _translate(BuildContext context, String fr, String en, String ar) {
  return switch (Localizations.localeOf(context).languageCode) {
    'ar' => ar,
    'en' => en,
    _ => fr,
  };
}

class _D2GuestShellState extends State<D2GuestShell> {
  int _selected = 0;

  @override
  Widget build(BuildContext context) {
    final destination = _destinations[_selected];
    final wide = MediaQuery.sizeOf(context).width >= 700;
    final label = _translate(
      context, destination.fr, destination.en, destination.ar,
    );

    return Scaffold(
      appBar: AppBar(
        title: Text(_translate(context, 'IAMINA · Visiteur',
            'IAMINA · Visitor', 'أمينة · زائر')),
      ),
      body: Row(
        children: [
          if (wide)
            NavigationRail(
              selectedIndex: _selected,
              onDestinationSelected: (index) =>
                  setState(() => _selected = index),
              labelType: NavigationRailLabelType.all,
              destinations: [
                for (final destination in _destinations)
                  NavigationRailDestination(
                    icon: Icon(
                      destination.icon,
                      key: Key('d2-guest-nav-${destination.id}'),
                    ),
                    label: Text(_translate(context, destination.fr,
                        destination.en, destination.ar)),
                  ),
              ],
            ),
          Expanded(
            child: SingleChildScrollView(
              child: Align(
                alignment: AlignmentDirectional.topCenter,
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 720),
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const SizedBox(height: 24),
                        Text(label, style: Theme.of(context).textTheme.headlineMedium),
                        const SizedBox(height: 16),
                        Text(
                          _translate(
                            context,
                            'Explorez cette rubrique librement. Vos données personnelles ne sont pas accessibles en mode visiteur.',
                            'Explore this section freely. Personal data is not available in visitor mode.',
                            'تصفّح هذا القسم بحرية. البيانات الشخصية غير متاحة في وضع الزائر.',
                          ),
                          key: const Key('d2-guest-empty-state'),
                          style: Theme.of(context).textTheme.bodyLarge,
                        ),
                        const SizedBox(height: 28),
                        Text(
                          _translate(
                            context,
                            'Pour utiliser cette fonction, connectez-vous ou créez un compte.',
                            'To use this feature, sign in or create an account.',
                            'لاستخدام هذه الميزة، سجّل الدخول أو أنشئ حسابًا.',
                          ),
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 12),
                        for (final action in _guestActions[destination.id]!)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: OutlinedButton.icon(
                              key: Key('d2-guest-action-${action.id}'),
                              icon: Icon(action.icon),
                              label: Text(_translate(context,
                                  action.fr, action.en, action.ar)),
                              onPressed: () =>
                                  widget.onProtectedAction(action.route),
                            ),
                          ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      bottomNavigationBar: wide
          ? null
          : NavigationBar(
              selectedIndex: _selected,
              onDestinationSelected: (index) =>
                  setState(() => _selected = index),
              destinations: [
                for (final destination in _destinations)
                  NavigationDestination(
                    icon: Icon(
                      destination.icon,
                      key: Key('d2-guest-nav-${destination.id}'),
                    ),
                    label: _translate(context, destination.fr,
                        destination.en, destination.ar),
                  ),
              ],
            ),
    );
  }
}
