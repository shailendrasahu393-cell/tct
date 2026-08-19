export const isValidUrl = value => { try { new URL(value); return true; } catch { return false; } };
export const passwordRequirements = value => ({
	length: value.length >= 8,
	lowercase: /\p{Ll}/u.test(value),
	uppercase: /\p{Lu}/u.test(value),
	number: /\p{N}/u.test(value),
});
export const passwordRules = value => Object.values(passwordRequirements(value)).every(Boolean);
export const passwordError = value => {
	const requirements = passwordRequirements(value);
	const missing = [];
	if (!requirements.length) missing.push('at least 8 characters');
	if (!requirements.uppercase) missing.push('one uppercase letter');
	if (!requirements.lowercase) missing.push('one lowercase letter');
	if (!requirements.number) missing.push('one number');
	return missing.length ? `Password needs ${missing.join(', ')}.` : '';
};
