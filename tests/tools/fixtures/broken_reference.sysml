// Deliberately broken (semantics): syntactically valid, but the type does not exist.
package BrokenReference {
    part def Controller {
        attribute speed : NoSuchType;
    }
}
