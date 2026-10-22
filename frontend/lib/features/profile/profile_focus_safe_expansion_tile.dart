import 'package:flutter/material.dart';

/// Keeps a Profile section's unsaved controls mounted while its panel is
/// collapsed, but removes those *invisible* controls from keyboard traversal.
///
/// ExpansionTile(maintainState: true) preserves offstage children. Offstage does
/// not itself prevent focus, so Tab can appear stuck on the last visible header
/// while it traverses hidden form fields. Do not lose form state by turning
/// maintainState off or by forcibly resetting the user's current focus.
class ProfileFocusSafeExpansionTile extends StatefulWidget {
  const ProfileFocusSafeExpansionTile({
    super.key,
    required this.title,
    required this.subtitle,
    required this.leading,
    required this.children,
    required this.initiallyExpanded,
    this.tilePadding,
    this.childrenPadding,
  });

  final Widget title;
  final Widget subtitle;
  final Widget leading;
  final List<Widget> children;
  final bool initiallyExpanded;
  final EdgeInsetsGeometry? tilePadding;
  final EdgeInsetsGeometry? childrenPadding;

  @override
  State<ProfileFocusSafeExpansionTile> createState() =>
      _ProfileFocusSafeExpansionTileState();
}

class _ProfileFocusSafeExpansionTileState
    extends State<ProfileFocusSafeExpansionTile> {
  late bool _expanded;

  @override
  void initState() {
    super.initState();
    _expanded = widget.initiallyExpanded;
  }

  @override
  Widget build(BuildContext context) {
    return ExpansionTile(
      maintainState: true,
      initiallyExpanded: widget.initiallyExpanded,
      onExpansionChanged: (expanded) {
        if (_expanded != expanded) {
          setState(() => _expanded = expanded);
        }
      },
      tilePadding: widget.tilePadding,
      childrenPadding: widget.childrenPadding,
      leading: widget.leading,
      title: widget.title,
      subtitle: widget.subtitle,
      children: [
        for (final child in widget.children)
          ExcludeFocus(excluding: !_expanded, child: child),
      ],
    );
  }
}
