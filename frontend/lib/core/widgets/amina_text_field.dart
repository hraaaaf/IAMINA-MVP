import 'package:flutter/material.dart';

import '../theme/amina_visual_language.dart';
import '../theme/app_theme.dart';

class AminaTextField extends StatefulWidget {
  final String label;
  final String hint;
  final TextEditingController controller;
  final bool obscureText;
  final TextInputType? keyboardType;
  final Widget? suffixIcon;
  final int? maxLines;

  const AminaTextField({
    super.key,
    required this.label,
    required this.hint,
    required this.controller,
    this.obscureText = false,
    this.keyboardType,
    this.suffixIcon,
    this.maxLines = 1,
  });

  @override
  State<AminaTextField> createState() => _AminaTextFieldState();
}

class _AminaTextFieldState extends State<AminaTextField> {
  final FocusNode _focusNode = FocusNode();
  bool _isFocused = false;

  @override
  void initState() {
    super.initState();
    _focusNode.addListener(() {
      if (mounted) setState(() => _isFocused = _focusNode.hasFocus);
    });
  }

  @override
  void dispose() {
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final labelColor = dark
        ? AminaTheme.dark200
        : AminaVisualLanguage.actionGreen;
    final focusColor = dark ? AminaTheme.teal400 : AminaTheme.teal500;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.label,
          style: TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 13,
            color: labelColor,
            letterSpacing: .05,
          ),
        ),
        const SizedBox(height: 5),
        AnimatedContainer(
          duration: const Duration(milliseconds: 160),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AminaVisualLanguage.fieldRadius),
            boxShadow: _isFocused
                ? [
                    BoxShadow(
                      color: focusColor.withValues(alpha: .11),
                      spreadRadius: 2,
                      blurRadius: 0,
                    ),
                  ]
                : null,
          ),
          child: TextField(
            focusNode: _focusNode,
            controller: widget.controller,
            obscureText: widget.obscureText,
            keyboardType: widget.keyboardType,
            maxLines: widget.maxLines,
            style: TextStyle(
              fontWeight: FontWeight.w500,
              fontSize: 13.5,
              color: AminaTheme.textPrimary(context),
            ),
            decoration: InputDecoration(
              hintText: widget.hint,
              hintStyle: TextStyle(
                color: AminaVisualLanguage.secondary(context),
                fontSize: 13.5,
              ),
              suffixIcon: widget.suffixIcon,
              contentPadding: const EdgeInsetsDirectional.fromSTEB(12, 10, 12, 10),
              filled: true,
              fillColor: AminaVisualLanguage.controlSurface(context),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AminaVisualLanguage.fieldRadius),
                borderSide: BorderSide(
                  color: AminaVisualLanguage.controlBorder(context),
                  width: 1.1,
                ),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AminaVisualLanguage.fieldRadius),
                borderSide: BorderSide(color: focusColor, width: 1.4),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
