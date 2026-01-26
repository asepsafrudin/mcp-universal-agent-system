# Code Review Checklist

## 🔍 **Pre-Review Preparation**
- [ ] Code compiles without errors
- [ ] Unit tests pass (if applicable)
- [ ] No console errors or warnings
- [ ] Code follows project conventions

## 🏗️ **Architecture & Design**
- [ ] Code follows single responsibility principle
- [ ] Functions/methods are appropriately sized (< 50 lines)
- [ ] No unnecessary complexity or over-engineering
- [ ] Proper separation of concerns
- [ ] Uses appropriate design patterns

## 🐛 **Bug Prevention**
- [ ] **ML Risk Assessment**: Risk score ≤ 0.5 (checked via quality monitor)
- [ ] Complexity score is reasonable for functionality
- [ ] No potential null pointer exceptions
- [ ] Proper error handling for all edge cases
- [ ] Input validation is implemented

## 🔒 **Security**
- [ ] No hardcoded secrets or credentials
- [ ] Input sanitization for user data
- [ ] No dangerous functions (eval, exec, etc.)
- [ ] SQL injection prevention (if applicable)
- [ ] XSS prevention (if applicable)

## 📝 **Code Quality**
- [ ] Meaningful variable and function names
- [ ] Consistent code formatting
- [ ] No dead code or unused imports
- [ ] Proper documentation/comments
- [ ] No print statements in production code

## 🧪 **Testing**
- [ ] Unit tests written for new functionality
- [ ] Edge cases are covered
- [ ] Integration tests pass
- [ ] No flaky tests

## 🚀 **Performance**
- [ ] No obvious performance bottlenecks
- [ ] Efficient algorithms used
- [ ] Memory leaks prevented
- [ ] Database queries optimized (if applicable)

## 📚 **Documentation**
- [ ] Code is self-documenting where possible
- [ ] Complex logic is commented
- [ ] API documentation updated (if applicable)
- [ ] README updated for new features

## 🔄 **Maintainability**
- [ ] Code is readable and understandable
- [ ] No magic numbers or hardcoded values
- [ ] Configuration externalized
- [ ] Dependencies are reasonable

## 🤝 **Collaboration**
- [ ] Follows team coding standards
- [ ] No merge conflicts
- [ ] Branch naming follows convention
- [ ] Commit messages are clear

## ✅ **Final Checks**
- [ ] **Quality Monitor**: Run `python scripts/quality_monitor.py`
- [ ] **ML Audit**: Risk score acceptable
- [ ] **Peer Review**: At least one other developer reviewed
- [ ] **Integration**: Code integrates well with existing codebase

---

## 📊 **Quality Gates**

### 🚫 **Blocking Issues (Must Fix)**
- Syntax errors
- Security vulnerabilities
- ML risk score > 0.7
- Test failures
- Breaking changes without migration

### ⚠️ **Warning Issues (Should Fix)**
- ML risk score 0.5-0.7
- Code style violations
- Missing documentation
- Performance concerns

### ✅ **Approved for Merge**
- All blocking issues resolved
- Warning issues addressed or justified
- Positive peer review
- Quality monitor passes (≥80% success rate)

---

## 🛠️ **Tools & Commands**

```bash
# Run quality monitoring
python scripts/quality_monitor.py

# Run ML audit
cd crew && python audit_mcp_server.py

# Check syntax
python -m py_compile <file.py>

# Run tests
python -m pytest
```

---

## 📞 **Escalation**

If unsure about any item:
1. Ask for clarification from team lead
2. Consult with senior developer
3. Reference project documentation
4. Check similar implementations in codebase

---

## 📈 **Continuous Improvement**

After each review cycle:
- [ ] Document lessons learned
- [ ] Update checklist if needed
- [ ] Share best practices with team
- [ ] Improve automated checks based on findings
