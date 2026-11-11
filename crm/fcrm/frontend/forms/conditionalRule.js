// Parsed, never run: a stored rule must not execute in the viewer's desk session.
// Keep the grammar and results equal to the public page's parser (crm/www/crm_form.html).

/** The rule's value for `doc`, or `fallback` when the rule is empty or does not parse. */
export function evaluateRule(expression, doc, fallback) {
	const rule = expression ? String(expression).trim() : "";
	if (!rule) return fallback;
	try {
		return truthy(rule, doc);
	} catch {
		return fallback;
	}
}

/** Why the rule does not parse, or null when it does (or is empty). */
export function ruleError(expression) {
	const rule = expression ? String(expression).trim() : "";
	if (!rule) return null;
	if (!rule.startsWith("eval:") && !rule.startsWith("fn:") && !FIELDNAME.test(rule))
		return "a rule that is not a field name starts with eval:";
	try {
		truthy(rule, {});
		return null;
	} catch (e) {
		return e.message;
	}
}

function truthy(rule, doc) {
	if (rule.startsWith("eval:")) return coerce(new RuleParser(rule.slice(5), doc).parse());
	if (rule.startsWith("fn:")) throw new Error("fn: rules do not run on public forms");
	return coerce(doc[rule]);
}

const COMPARISONS = ["===", "!==", "==", "!=", "<=", ">=", "<", ">"];
const IDENTIFIER = /^[A-Za-z_$][\w$]*/;
const FIELDNAME = /^[A-Za-z_]\w*$/;
const NUMBER = /^-?\d+(?:\.\d+)?/;

/** Reads `doc` / `parent` members, literals, comparisons, `&&`, `||`, `!` and parentheses. */
class RuleParser {
	constructor(source, doc) {
		this.source = source;
		this.doc = doc;
		this.at = 0;
	}

	parse() {
		const value = this.or();
		this.skipSpace();
		if (this.at < this.source.length) throw new Error("unexpected text after the rule");
		return value;
	}

	or() {
		let left = this.and();
		while (this.startsWith("||")) {
			this.at += 2;
			const right = this.and();
			left = coerce(left) || coerce(right);
		}
		return left;
	}

	and() {
		let left = this.comparison();
		while (this.startsWith("&&")) {
			this.at += 2;
			const right = this.comparison();
			left = coerce(left) && coerce(right);
		}
		return left;
	}

	comparison() {
		const left = this.primary();
		this.skipSpace();
		const op = COMPARISONS.find((candidate) => this.source.startsWith(candidate, this.at));
		if (!op) return left;
		this.at += op.length;
		return compare(op, left, this.primary());
	}

	primary() {
		if (this.startsWith("(")) {
			this.at++;
			const value = this.or();
			this.expect(")");
			return value;
		}
		if (this.startsWith("!")) {
			this.at++;
			return !coerce(this.primary());
		}
		const quote = this.source[this.at];
		if (quote === '"' || quote === "'") return this.string(quote);
		const number = NUMBER.exec(this.source.slice(this.at));
		if (number) {
			this.at += number[0].length;
			return parseFloat(number[0]);
		}
		return this.reference();
	}

	reference() {
		const name = this.identifier("unexpected token");
		if (Object.hasOwn(LITERALS, name)) return LITERALS[name];
		// Only the record is in scope: no global is reachable.
		if (name !== "doc" && name !== "parent") throw new Error(`unknown name: ${name}`);
		let value = this.doc;
		for (;;) {
			this.skipSpace();
			if (this.source[this.at] === ".") {
				this.at++;
				value = member(value, this.identifier("bad member"));
			} else if (this.source[this.at] === "[") {
				this.at++;
				const key = this.or();
				this.expect("]");
				value = member(value, key);
			} else return value;
		}
	}

	string(quote) {
		this.at++;
		let text = "";
		while (this.at < this.source.length && this.source[this.at] !== quote) {
			if (this.source[this.at] === "\\") this.at++;
			text += this.source[this.at++];
		}
		this.at++;
		return text;
	}

	identifier(error) {
		const match = IDENTIFIER.exec(this.source.slice(this.at));
		if (!match) throw new Error(error);
		this.at += match[0].length;
		return match[0];
	}

	expect(token) {
		if (!this.startsWith(token)) throw new Error(`expected ${token}`);
		this.at += token.length;
	}

	startsWith(token) {
		this.skipSpace();
		return this.source.startsWith(token, this.at);
	}

	skipSpace() {
		while (this.at < this.source.length && /\s/.test(this.source[this.at])) this.at++;
	}
}

const LITERALS = { true: true, false: false, null: null };

function member(value, key) {
	return value == null ? undefined : value[key];
}

function compare(op, left, right) {
	switch (op) {
		case "===":
		case "==":
			return left == right; // eslint-disable-line eqeqeq
		case "!==":
		case "!=":
			return left != right; // eslint-disable-line eqeqeq
		case "<":
			return left < right;
		case "<=":
			return left <= right;
		case ">":
			return left > right;
		default:
			return left >= right;
	}
}

function coerce(value) {
	return Array.isArray(value) ? value.length > 0 : !!value;
}
