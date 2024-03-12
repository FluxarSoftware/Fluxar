"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.activate = void 0;
const vscode = require("vscode");
function activate(context) {
    const mainProvider = vscode.languages.registerCompletionItemProvider('fluxar', {
        provideCompletionItems(document, position, token, context) {
            // a simple completion item which inserts `Hello World!`
            const simpleCompletion = new vscode.CompletionItem('Hello World!');
            // a completion item that inserts its text as snippet,
            // the `insertText`-property is a `SnippetString` which will be
            // honored by the editor.
            const snippetCompletion = new vscode.CompletionItem('Good part of the day');
            snippetCompletion.insertText = new vscode.SnippetString('Good ${1|morning,afternoon,evening|}. It is ${1}, right?');
            const docs = new vscode.MarkdownString("Inserts a snippet that lets you select [link](x.ts).");
            snippetCompletion.documentation = docs;
            docs.baseUri = vscode.Uri.parse('http://example.com/a/b/c/');
            // a completion item that can be accepted by a commit character,
            // the `commitCharacters`-property is set which means that the completion will
            // be inserted and then the character will be typed.
            const tableSnippet = new vscode.CompletionItem('table');
            tableSnippet.commitCharacters = ['.'];
            tableSnippet.documentation = new vscode.MarkdownString('Press `.` to get `console.`');
            // a completion item that retriggers IntelliSense when being accepted,
            // the `command`-property is set which the editor will execute after 
            // completion has been inserted. Also, the `insertText` is set so that 
            // a space is inserted after `new`
            const commandCompletion = new vscode.CompletionItem('new');
            commandCompletion.kind = vscode.CompletionItemKind.Keyword;
            commandCompletion.insertText = 'new ';
            commandCompletion.command = { command: 'editor.action.triggerSuggest', title: 'Re-trigger completions...' };
            // return all completion items as array
            return [
                simpleCompletion,
                snippetCompletion,
                tableSnippet,
                commandCompletion
            ];
        }
    });
    const tableFuncProvider = vscode.languages.registerCompletionItemProvider('fluxar', {
        provideCompletionItems(document, position) {
            // get all text until the `position` and check if it reads `table.`
            const linePrefix = document.lineAt(position).text.slice(0, position.character);
            if (!linePrefix.endsWith('table.')) {
                return undefined;
            }
            // Create completion items
            const completionItems = [
                new vscode.CompletionItem('insert', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('remove', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('extend', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('clear', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('concat', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('find', vscode.CompletionItemKind.Method),
                new vscode.CompletionItem('len', vscode.CompletionItemKind.Method),
            ];
            // Add documentation or descriptions to completion items
            completionItems.forEach(item => {
                switch (item.label) {
                    case 'insert':
                        item.documentation = new vscode.MarkdownString('Inserts an element into a list at the specified position.');
                        break;
                    case 'remove':
                        item.documentation = new vscode.MarkdownString('Removes the element at the specified position from a list.');
                        break;
                    case 'extend':
                        item.documentation = new vscode.MarkdownString('Extends a list by appending elements from another list.');
                        break;
                    // Add descriptions for other completion items as needed
                }
            });
            return completionItems;
        }
    }, '.' // triggered whenever a '.' is being typed
    );
    context.subscriptions.push(mainProvider, tableFuncProvider);
}
exports.activate = activate;
//# sourceMappingURL=extension.js.map