export class Calculator {
    constructor() {
        this.result = 0;
    }

    add(x) {
        this.result += x;
        return this;
    }

    subtract(x) {
        this.result -= x;
        return this;
    }

    getResult() {
        return this.result;
    }

    clear() {
        this.result = 0;
        return this;
    }
}

export function parseJSON(str) {
    return JSON.parse(str);
}
