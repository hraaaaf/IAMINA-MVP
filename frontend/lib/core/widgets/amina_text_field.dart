import 'package:flutter/material.dart';
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
      setState(() {
        _isFocused = _focusNode.hasFocus;
      });
    });
  }

  @override
  void dispose() {
    _focusNode.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          widget.label,
          style: const TextStyle(
            fontWeight: FontWeight.w600,
            fontSize: 13,
            color: AminaTheme.textMuted,
            letterSpacing: 0.2,
          ),
        ),
        const SizedBox(height: 6),
        AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
            boxShadow: _isFocused 
              ? [
                  BoxShadow(
                    color: AminaTheme.primaryTeal.withValues(alpha: 0.15),
                    spreadRadius: 3,
                    blurRadius: 0,
                  )
                ]
              : null,
          ),
          child: TextField(
            focusNode: _focusNode,
            controller: widget.controller,
            obscureText: widget.obscureText,
            keyboardType: widget.keyboardType,
            maxLines: widget.maxLines,
            style: const TextStyle(fontWeight: FontWeight.w500),
            decoration: InputDecoration(
              hintText: widget.hint,
              hintStyle: const TextStyle(color: AminaTheme.textLight, fontSize: 14),
              suffixIcon: widget.suffixIcon,
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 15),
              filled: true,
              fillColor: Colors.white,
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                borderSide: const BorderSide(color: AminaTheme.borderLight, width: 2),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(AminaTheme.radiusXL),
                borderSide: const BorderSide(color: AminaTheme.primaryTeal, width: 2),
              ),
            ),
          ),
        ),
      ],
    );
  }
}
