import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

class OtpCodeInput extends StatefulWidget {
  const OtpCodeInput({
    super.key,
    required this.onChanged,
    this.autofocus = false,
  });

  final ValueChanged<String> onChanged;
  final bool autofocus;

  @override
  State<OtpCodeInput> createState() => _OtpCodeInputState();
}

class _OtpCodeInputState extends State<OtpCodeInput> {
  final _controllers = List.generate(4, (_) => TextEditingController());
  final _focusNodes = List.generate(4, (_) => FocusNode());

  @override
  void dispose() {
    for (final controller in _controllers) {
      controller.dispose();
    }
    for (final focusNode in _focusNodes) {
      focusNode.dispose();
    }
    super.dispose();
  }

  void _onDigitChanged(int index, String value) {
    final digits = value.replaceAll(RegExp(r'\D'), '');
    if (digits.length > 1) {
      for (final controller in _controllers) {
        controller.clear();
      }
      for (var offset = 0; offset < digits.length && index + offset < 4; offset++) {
        final controller = _controllers[index + offset];
        controller.value = TextEditingValue(
          text: digits[offset],
          selection: const TextSelection.collapsed(offset: 1),
        );
      }
      _focusNodes[(index + digits.length).clamp(0, 3).toInt()].requestFocus();
    } else {
      if (_controllers[index].text != digits) _controllers[index].text = digits;
      if (digits.isNotEmpty && index < 3) {
        _focusNodes[index + 1].requestFocus();
      } else if (digits.isEmpty && index > 0) {
        _focusNodes[index - 1].requestFocus();
      }
    }
    widget.onChanged(_controllers.map((controller) => controller.text).join());
  }

  @override
  Widget build(BuildContext context) => Row(
    children: [
      for (var index = 0; index < 4; index++) ...[
        if (index > 0) const SizedBox(width: 10),
        Expanded(
          child: SizedBox(
            height: 58,
            child: TextField(
              controller: _controllers[index],
              focusNode: _focusNodes[index],
              autofocus: widget.autofocus && index == 0,
              keyboardType: TextInputType.number,
              textInputAction: index == 3 ? TextInputAction.done : TextInputAction.next,
              textAlign: TextAlign.center,
              autofillHints: index == 0 ? const [AutofillHints.oneTimeCode] : null,
              inputFormatters: [FilteringTextInputFormatter.digitsOnly],
              maxLength: 4,
              style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800),
              decoration: const InputDecoration(counterText: '', contentPadding: EdgeInsets.zero),
              onChanged: (value) => _onDigitChanged(index, value),
            ),
          ),
        ),
      ],
    ],
  );
}
