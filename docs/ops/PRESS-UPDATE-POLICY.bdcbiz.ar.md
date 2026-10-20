# BDC deployment policy for self-hosted Press

This policy applies only to bdcbiz self-hosted Press deployments of this app. Upstream development, contribution, testing and release workflows remain unchanged. The following organization-specific policy does not authorize deployments or changes to upstream infrastructure.

## سياسة تحديث Press: التحديث في المكان أولًا
كل تحديث كود لتطبيق موجود على bench قائم يمر عبر In-place update في Press وفق [السياسة المركزية](https://github.com/bdcbiz/almadrasa-press-infra/blob/main/docs/ops/PRESS-UPDATE-POLICY.ar.md).
التفعيل مشروط بنجاح staging على bench-0005 ثم موقع إنتاجي واحد؛ حتى تنجح التجربتان يبقى البناء الكامل.
البناء الكامل للحالات غير المدعومة أو التي يمنعها التحفظ وفق السياسة؛ وتغييرات التبعيات تتطلب staging أولًا.
صنّف الفرق الكامل بين SHA المنشور والهدف، واحجز bench ومواقعه وموارده المشتركة في LIVE-WRITER؛ bench واحد في كل مرة.
قبل migrate: نسخة حديثة مع اختبار استرجاع معزول وفحص الأقفال؛ وثّق last-good image وdigest واحمِها من GC.
تحقق من نجاح Agent Job وتطابق hashes وصحة العمليات وsmoke tests؛ عند الفشل استعد وتحقق من قاعدة البيانات ولا تعاود قبل المراجعة.
ممنوع تعديل الكود يدويًا داخل الحاويات؛ كل دمج عبر PR ومراجعة مستقلة، بلا force-push أو --no-verify أو أسرار.
