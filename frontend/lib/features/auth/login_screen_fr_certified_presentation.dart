part of 'login_screen_fr_certified.dart';

class _LoginBackdrop extends StatelessWidget {
  const _LoginBackdrop();
  @override
  Widget build(BuildContext context) {
    return IgnorePointer(
      child: CustomPaint(
        painter: _LoginBackdropPainter(isDark: AminaTheme.isDark(context)),
      ),
    );
  }
}

class _BottomWave extends StatelessWidget {
  const _BottomWave();
  @override
  Widget build(BuildContext context) {
    if (AminaTheme.isDark(context)) return const SizedBox.shrink();
    return Align(
      alignment: Alignment.bottomCenter,
      child: IgnorePointer(
        child: ClipPath(
          clipper: const _BottomWaveClipper(),
          child: Container(
            height: 90,
            decoration: const BoxDecoration(
              gradient: LinearGradient(
                colors: [Color(0xFFDDF8F3), Color(0xFFA8E9DE)],
                begin: AlignmentDirectional.topStart,
                end: AlignmentDirectional.bottomEnd,
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _BottomWaveClipper extends CustomClipper<Path> {
  const _BottomWaveClipper();
  @override
  Path getClip(Size size) => Path()
    ..moveTo(0, size.height * .45)
    ..cubicTo(
      size.width * .20,
      size.height * .32,
      size.width * .43,
      size.height * .78,
      size.width * .66,
      size.height * .52,
    )
    ..cubicTo(
      size.width * .82,
      size.height * .34,
      size.width * .94,
      size.height * .18,
      size.width,
      size.height * .14,
    )
    ..lineTo(size.width, size.height)
    ..lineTo(0, size.height)
    ..close();

  @override
  bool shouldReclip(covariant _BottomWaveClipper oldClipper) => false;
}

class _LoginBackdropPainter extends CustomPainter {
  final bool isDark;
  const _LoginBackdropPainter({required this.isDark});
  @override
  void paint(Canvas canvas, Size size) {
    canvas.drawRect(
      Offset.zero & size,
      Paint()..color = isDark ? AminaTheme.darkPaper : AminaTheme.paper,
    );
    if (isDark) return;
    void glow(Offset center, double radius, Color color) {
      canvas.drawCircle(
        center,
        radius,
        Paint()
          ..shader = RadialGradient(
            colors: [color, color.withValues(alpha: .16), Colors.transparent],
            stops: const [0, .48, 1],
          ).createShader(Rect.fromCircle(center: center, radius: radius)),
      );
    }

    glow(
      Offset(-size.width * .08, size.height * .18),
      size.width * .38,
      const Color(0x4028D8C2),
    );
    glow(
      Offset(size.width * 1.04, size.height * .20),
      size.width * .24,
      const Color(0x3837E4D0),
    );
    glow(
      Offset(size.width * 1.00, size.height * .72),
      size.width * .22,
      const Color(0x2228D8C2),
    );
  }

  @override
  bool shouldRepaint(covariant _LoginBackdropPainter oldDelegate) =>
      oldDelegate.isDark != isDark;
}

class _Brand extends StatelessWidget {
  const _Brand();
  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final logo = kIsWeb
        ? Image.network(
            'assets/assets/images/logo_amina.png',
            fit: BoxFit.contain,
            webHtmlElementStrategy: WebHtmlElementStrategy.fallback,
            errorBuilder: (_, __, ___) => const _BrandFallback(),
          )
        : Image.asset(
            'assets/images/logo_amina.png',
            fit: BoxFit.contain,
            filterQuality: FilterQuality.high,
            errorBuilder: (_, __, ___) => const _BrandFallback(),
          );
    return Semantics(
      label: l10n.appTitle,
      image: true,
      child: SizedBox(width: 140, height: 176, child: logo),
    );
  }
}

class _BrandFallback extends StatelessWidget {
  const _BrandFallback();
  @override
  Widget build(BuildContext context) {
    return const Column(
      mainAxisAlignment: MainAxisAlignment.center,
      children: [
        Text(
          'IA',
          style: TextStyle(
            fontFamily: 'Georgia',
            fontSize: 58,
            height: .92,
            fontWeight: FontWeight.w600,
            color: Color(0xFF075A45),
          ),
        ),
        SizedBox(height: 6),
        Text(
          'آمينة',
          textDirection: TextDirection.rtl,
          style: TextStyle(
            fontSize: 35,
            height: 1,
            fontWeight: FontWeight.w500,
            color: Color(0xFF075A45),
          ),
        ),
      ],
    );
  }
}

class _LoginCard extends StatelessWidget {
  final TextEditingController emailCtrl;
  final TextEditingController passwordCtrl;
  final bool obscure;
  final VoidCallback onToggleObscure;
  final String? error;
  final bool isLoading;
  final void Function({bool isDemo}) onSubmit;
  final VoidCallback onForgotPassword;
  final VoidCallback onDemo;
  final VoidCallback onSignup;
  final String welcome;
  final String subtitle;
  final String demoLabel;
  const _LoginCard({
    required this.emailCtrl,
    required this.passwordCtrl,
    required this.obscure,
    required this.onToggleObscure,
    required this.error,
    required this.isLoading,
    required this.onSubmit,
    required this.onForgotPassword,
    required this.onDemo,
    required this.onSignup,
    required this.welcome,
    required this.subtitle,
    required this.demoLabel,
  });

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context)!;
    final dark = AminaTheme.isDark(context);
    return Container(
      padding: const EdgeInsetsDirectional.fromSTEB(26, 20, 26, 20),
      decoration: BoxDecoration(
        color: AminaTheme.surface(context).withValues(alpha: dark ? .98 : .975),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: dark
              ? AminaTheme.divider(context).withValues(alpha: .58)
              : Colors.white.withValues(alpha: .90),
        ),
        boxShadow: dark
            ? AminaTheme.shadowDark
            : const [
                BoxShadow(
                  color: Color(0x1B11423A),
                  blurRadius: 32,
                  spreadRadius: -8,
                  offset: Offset(0, 15),
                ),
                BoxShadow(
                  color: Color(0x0D0D1A17),
                  blurRadius: 12,
                  spreadRadius: -4,
                  offset: Offset(0, 5),
                ),
              ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text(
            welcome,
            style: TextStyle(
              fontFamily: 'Georgia',
              fontFamilyFallback: const ['Times New Roman', 'serif'],
              fontSize: 30,
              height: 1.08,
              fontWeight: FontWeight.w700,
              letterSpacing: -.7,
              color: dark ? AminaTheme.dark100 : const Color(0xFF073D31),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            subtitle,
            style: TextStyle(
              fontSize: 13,
              height: 1.35,
              color: dark ? AminaTheme.dark300 : const Color(0xFF566B68),
            ),
          ),
          const SizedBox(height: 16),
          _FieldLabel(l10n.emailLabel),
          const SizedBox(height: 5),
          _Field(
            controller: emailCtrl,
            hint: l10n.emailPlaceholder,
            keyboardType: TextInputType.emailAddress,
            prefix: const Icon(Icons.mail_outline_rounded),
          ),
          const SizedBox(height: 15),
          _FieldLabel(l10n.passwordLabel),
          const SizedBox(height: 5),
          _Field(
            controller: passwordCtrl,
            hint: '••••••••••••',
            obscureText: obscure,
            prefix: const Icon(Icons.lock_outline_rounded),
            suffix: IconButton(
              onPressed: onToggleObscure,
              icon: Icon(
                obscure
                    ? Icons.visibility_outlined
                    : Icons.visibility_off_outlined,
                size: 19,
                color: AminaTheme.ink400,
              ),
            ),
            onSubmit: (_) => onSubmit(),
          ),
          Align(
            alignment: AlignmentDirectional.centerEnd,
            child: TextButton(
              onPressed: onForgotPassword,
              style: TextButton.styleFrom(
                padding: const EdgeInsetsDirectional.fromSTEB(6, 0, 0, 0),
                minimumSize: const Size(44, 32),
                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
              child: Text(
                l10n.forgotPassword,
                style: const TextStyle(
                  fontSize: 12.5,
                  color: Color(0xFF0B735F),
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ),
          if (error != null) ...[
            const SizedBox(height: 4),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 7),
              decoration: BoxDecoration(
                color: AminaTheme.dangerBg,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  const Icon(
                    Icons.error_outline,
                    size: 14,
                    color: AminaTheme.dangerFg,
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      error!,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AminaTheme.dangerFg,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
          const SizedBox(height: 13),
          _PrimaryLoginButton(
            isLoading: isLoading,
            label: l10n.signIn,
            onTap: () => onSubmit(),
          ),
          const SizedBox(height: 6),
          _DividerOr(label: l10n.or),
          const SizedBox(height: 6),
          _DemoButton(isLoading: isLoading, label: demoLabel, onTap: onDemo),
          const SizedBox(height: 8),
          _SignupRow(isLoading: isLoading, onTap: onSignup),
        ],
      ),
    );
  }
}

class _FieldLabel extends StatelessWidget {
  final String text;
  const _FieldLabel(this.text);
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    return Text(
      text,
      style: TextStyle(
        fontSize: 13.2,
        fontWeight: FontWeight.w600,
        color: dark ? AminaTheme.dark200 : const Color(0xFF075A45),
      ),
    );
  }
}

class _Field extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final bool obscureText;
  final TextInputType? keyboardType;
  final Widget? prefix;
  final Widget? suffix;
  final void Function(String)? onSubmit;
  const _Field({
    required this.controller,
    required this.hint,
    this.obscureText = false,
    this.keyboardType,
    this.prefix,
    this.suffix,
    this.onSubmit,
  });
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final iconColor = dark ? AminaTheme.dark300 : const Color(0xFF0B735F);
    return SizedBox(
      height: 36,
      child: TextField(
        controller: controller,
        obscureText: obscureText,
        keyboardType: keyboardType,
        onSubmitted: onSubmit,
        style: TextStyle(
          fontSize: 13.5,
          color: dark ? AminaTheme.dark100 : AminaTheme.ink900,
        ),
        decoration: InputDecoration(
          hintText: hint,
          hintStyle: TextStyle(
            color: AminaTheme.textSecondary(context),
            fontSize: 13.5,
          ),
          filled: true,
          fillColor: dark
              ? AminaTheme.darkCard
              : Colors.white.withValues(alpha: .92),
          contentPadding: const EdgeInsetsDirectional.fromSTEB(12, 8, 12, 8),
          prefixIcon: prefix == null
              ? null
              : IconTheme(
                  data: IconThemeData(size: 18, color: iconColor),
                  child: prefix!,
                ),
          prefixIconConstraints: const BoxConstraints(
            minWidth: 38,
            minHeight: 36,
          ),
          suffixIcon: suffix,
          suffixIconConstraints: const BoxConstraints(
            minWidth: 38,
            minHeight: 36,
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: Color(0xFFC5CECC), width: 1.1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(color: AminaTheme.teal500, width: 1.4),
          ),
          errorBorder: OutlineInputBorder(
            borderRadius: BorderRadius.circular(10),
            borderSide: const BorderSide(
              color: AminaTheme.dangerFg,
              width: 1.2,
            ),
          ),
        ),
      ),
    );
  }
}

class _PrimaryLoginButton extends StatelessWidget {
  final bool isLoading;
  final String label;
  final VoidCallback onTap;
  const _PrimaryLoginButton({
    required this.isLoading,
    required this.label,
    required this.onTap,
  });
  @override
  Widget build(BuildContext context) {
    return DecoratedBox(
      decoration: BoxDecoration(
        gradient: const RadialGradient(
          center: Alignment(0, -0.65),
          radius: 1.25,
          colors: [Color(0xFF087159), Color(0xFF04503F), Color(0xFF023A2E)],
          stops: [0, .62, 1],
        ),
        borderRadius: BorderRadius.circular(12),
        boxShadow: const [
          BoxShadow(
            color: Color(0x35034A39),
            blurRadius: 18,
            spreadRadius: -6,
            offset: Offset(0, 9),
          ),
        ],
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        child: InkWell(
          onTap: isLoading ? null : onTap,
          borderRadius: BorderRadius.circular(12),
          child: SizedBox(
            height: 42,
            child: Center(
              child: isLoading
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(
                        strokeWidth: 2,
                        color: Colors.white,
                      ),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.lock_outline_rounded,
                          size: 17,
                          color: Colors.white,
                        ),
                        const SizedBox(width: 9),
                        Text(
                          label,
                          style: const TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w700,
                            color: Colors.white,
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DividerOr extends StatelessWidget {
  final String label;
  const _DividerOr({required this.label});
  @override
  Widget build(BuildContext context) {
    final divider = AminaTheme.divider(context);
    return Row(
      children: [
        Expanded(child: Divider(color: divider, height: 1)),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 9),
          child: Container(
            width: 24,
            height: 24,
            alignment: Alignment.center,
            decoration: BoxDecoration(
              color: AminaTheme.surface(context),
              shape: BoxShape.circle,
              border: Border.all(color: divider),
            ),
            child: Text(
              label,
              style: TextStyle(
                fontSize: 11,
                color: AminaTheme.textSecondary(context),
              ),
            ),
          ),
        ),
        Expanded(child: Divider(color: divider, height: 1)),
      ],
    );
  }
}

class _DemoButton extends StatelessWidget {
  final bool isLoading;
  final String label;
  final VoidCallback onTap;
  const _DemoButton({
    required this.isLoading,
    required this.label,
    required this.onTap,
  });
  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 40,
      child: OutlinedButton.icon(
        onPressed: isLoading ? null : onTap,
        icon: const Icon(
          Icons.eco_outlined,
          size: 17,
          color: Color(0xFF075F4A),
        ),
        label: Text(
          label,
          style: const TextStyle(
            color: Color(0xFF075F4A),
            fontWeight: FontWeight.w700,
            fontSize: 13.5,
          ),
        ),
        style: OutlinedButton.styleFrom(
          side: const BorderSide(color: Color(0xFF0B735F), width: 1.15),
          backgroundColor: AminaTheme.surface(context).withValues(alpha: .88),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
        ),
      ),
    );
  }
}

class _SignupRow extends StatelessWidget {
  final bool isLoading;
  final VoidCallback onTap;
  const _SignupRow({required this.isLoading, required this.onTap});
  @override
  Widget build(BuildContext context) {
    return Wrap(
      alignment: WrapAlignment.center,
      crossAxisAlignment: WrapCrossAlignment.center,
      spacing: 2,
      children: [
        Text(
          'Pas encore de compte ?',
          style: TextStyle(
            fontSize: 12.8,
            color: AminaTheme.textSecondary(context),
          ),
        ),
        TextButton(
          onPressed: isLoading ? null : onTap,
          style: TextButton.styleFrom(
            minimumSize: const Size(44, 34),
            padding: const EdgeInsetsDirectional.fromSTEB(5, 0, 5, 0),
            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
          ),
          child: const Text(
            'Créer un compte',
            style: TextStyle(
              fontSize: 12.8,
              fontWeight: FontWeight.w500,
              color: Color(0xFF0B735F),
              decoration: TextDecoration.underline,
              decorationThickness: 1.1,
            ),
          ),
        ),
      ],
    );
  }
}

class _Footer extends StatelessWidget {
  final String label;
  const _Footer({required this.label});
  @override
  Widget build(BuildContext context) {
    final dark = AminaTheme.isDark(context);
    final foreground = dark ? AminaTheme.dark300 : const Color(0xFF526865);
    return ConstrainedBox(
      constraints: const BoxConstraints(maxWidth: 260),
      child: Column(
        children: [
          Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: const Color(
                0xFFE4F7F2,
              ).withValues(alpha: dark ? .10 : .92),
              shape: BoxShape.circle,
              border: Border.all(
                color: const Color(
                  0xFFB8E9DE,
                ).withValues(alpha: dark ? .38 : .78),
              ),
            ),
            child: Icon(
              Icons.shield_outlined,
              size: 21,
              color: dark ? AminaTheme.teal400 : const Color(0xFF0B735F),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            label,
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 11.5, height: 1.34, color: foreground),
          ),
        ],
      ),
    );
  }
}

